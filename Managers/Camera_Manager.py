#!/usr/bin/env python3
"""
Camera_Manager.py

High-level camera manager for Jetson Orin Nano following jetson-hardware patterns.
Provides thread-safe camera access with file locking and real-time capture capabilities.

Author: AI Assistant  
Date: 2025-10-25
Hardware: NVIDIA Jetson Orin Nano with JetPack 6.0
Cameras: USB 2.0 Camera, Future IMX708 CSI support
"""

import fcntl
import json
import logging
import os

# Add project root to Python path
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.append('/home/phiip/workspace/jetson-hardware')

import numpy as np

from Libs.CameraLib import CameraInfo, CameraLib, CameraType


class CameraManager:
    """
    Thread-safe camera manager for Jetson Orin Nano.
    
    Provides exclusive access to camera devices with file locking,
    real-time capture, and integration with Display_Manager for live preview.
    """
    
    # Class-level thread lock for exclusive access
    _lock = threading.Lock()
    
    def __init__(self, log_path: str = None, default_camera: int = 0):
        """
        Initialize Camera Manager.
        
        Args:
            log_path: Path to log file (optional)
            default_camera: Default camera device ID
        """
        # Camera library
        self.camera_lib = CameraLib()
        
        # State management
        self._acquired = False
        self._camera_opened = False
        self._current_camera_id = default_camera
        self._capture_active = False
        self._capture_thread = None
        
        # File locking for process-level exclusivity
        self._lock_file = '/tmp/camera_manager.lock'
        self._lock_fd = None
        
        # Performance tracking
        self._frame_count = 0
        self._fps_counter = 0
        self._last_update_time = time.time()
        
        # Camera information cache
        self._available_cameras = []
        self._camera_info_cache = {}
        
        # Setup logging
        self._setup_logging(log_path)
        
    def _setup_logging(self, log_path: str = None):
        """Setup logging configuration."""
        if log_path is None:
            log_path = '/home/phiip/workspace/jetson-hardware/Managers/logs/camera_manager.log'
        
        # Ensure log directory exists
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger(f"{__name__}_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler(log_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def acquire(self) -> bool:
        """
        Acquire exclusive access to camera resources.
        
        Returns:
            bool: True if acquisition successful
        """
        try:
            # Thread-level lock
            CameraManager._lock.acquire()
            
            # Process-level file lock
            self._lock_fd = open(self._lock_file, 'w')
            fcntl.lockf(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            self._acquired = True
            self.logger.info("Camera manager acquired (thread + file lock)")
            
            # Discover available cameras
            self._discover_cameras()
            
            return True
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to acquire camera manager (resource busy): {e}")
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            CameraManager._lock.release()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error acquiring camera manager: {e}")
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            CameraManager._lock.release()
            return False
    
    def release(self):
        """Release camera resources and cleanup."""
        try:
            if self._capture_active:
                self.stop_capture()
            
            if self._camera_opened:
                self.close_camera()
            
            # Release file lock
            if self._lock_fd:
                try:
                    fcntl.lockf(self._lock_fd, fcntl.LOCK_UN)
                    self._lock_fd.close()
                except:
                    pass
                self._lock_fd = None
            
            # Clean up lock file
            try:
                os.unlink(self._lock_file)
            except:
                pass
            
            # Release thread lock
            try:
                CameraManager._lock.release()
            except:
                pass
            
            self.logger.info("Camera manager released")
            
        except Exception as e:
            self.logger.error(f"Error releasing camera manager: {e}")
        
        self._acquired = False
    
    def _check_acquired(self):
        """Check if manager is acquired, raise exception if not."""
        if not self._acquired:
            raise RuntimeError("Must acquire CameraManager before use")
    
    def _discover_cameras(self):
        """Discover available cameras and cache information."""
        try:
            self._available_cameras = self.camera_lib.discover_cameras()
            self.logger.info(f"Discovered {len(self._available_cameras)} cameras")
            
            for camera in self._available_cameras:
                self.logger.info(f"Camera {camera.device_id}: {camera.name} ({camera.camera_type.value})")
                
        except Exception as e:
            self.logger.error(f"Error discovering cameras: {e}")
            self._available_cameras = []
    
    def list_cameras(self) -> List[Dict[str, Any]]:
        """
        List available cameras.
        
        Returns:
            List[Dict[str, Any]]: Camera information
        """
        self._check_acquired()
        
        camera_list = []
        for camera in self._available_cameras:
            camera_dict = {
                'device_id': camera.device_id,
                'name': camera.name,
                'type': camera.camera_type.value,
                'supported_resolutions': camera.supported_resolutions,
                'supported_formats': camera.supported_formats,
                'is_available': camera.is_available
            }
            camera_list.append(camera_dict)
        
        return camera_list
    
    def open_camera(self, camera_id: int = 0, width: int = 640, height: int = 480, 
                   fps: int = 30) -> bool:
        """
        Open camera for capture.
        
        Args:
            camera_id: Camera device ID
            width: Capture width
            height: Capture height
            fps: Desired framerate
            
        Returns:
            bool: True if camera opened successfully
        """
        self._check_acquired()
        
        try:
            if self._camera_opened:
                self.logger.warning("Camera already opened, closing previous connection")
                self.close_camera()
            
            success = self.camera_lib.open_camera(camera_id, width, height, fps)
            if success:
                self._camera_opened = True
                self._current_camera_id = camera_id
                self._frame_count = 0
                self._last_update_time = time.time()
                
                # Cache camera info
                self._camera_info_cache = self.camera_lib.get_camera_info()
                
                self.logger.info(f"Camera {camera_id} opened successfully")
                return True
            else:
                self.logger.error(f"Failed to open camera {camera_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error opening camera {camera_id}: {e}")
            return False
    
    def close_camera(self) -> bool:
        """
        Close current camera.
        
        Returns:
            bool: True if closed successfully
        """
        self._check_acquired()
        
        try:
            if self._capture_active:
                self.stop_capture()
            
            success = self.camera_lib.close_camera()
            if success:
                self._camera_opened = False
                self._current_camera_id = None
                self._camera_info_cache = {}
                self.logger.info("Camera closed successfully")
                return True
            else:
                self.logger.error("Failed to close camera")
                return False
                
        except Exception as e:
            self.logger.error(f"Error closing camera: {e}")
            return False
    
    def capture_frame(self) -> np.ndarray | None:
        """
        Capture a single frame from the camera.
        
        Returns:
            Optional[np.ndarray]: BGR image frame, None if failed
        """
        self._check_acquired()
        
        if not self._camera_opened:
            self.logger.error("No camera opened for frame capture")
            return None
        
        try:
            frame = self.camera_lib.capture_frame()
            if frame is not None:
                self._update_fps_counter()
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def save_image(self, filename: str, frame: np.ndarray | None = None) -> bool:
        """
        Save current frame or provided frame to file.
        
        Args:
            filename: Output filename
            frame: Frame to save (None = capture new frame)
            
        Returns:
            bool: True if saved successfully
        """
        self._check_acquired()
        
        try:
            if frame is None:
                frame = self.capture_frame()
                
            if frame is None:
                self.logger.error("No frame available to save")
                return False
            
            success = self.camera_lib.save_image(filename, frame)
            if success:
                self.logger.info(f"Image saved to {filename}")
                return True
            else:
                self.logger.error(f"Failed to save image to {filename}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving image {filename}: {e}")
            return False
    
    def start_capture(self, callback: Callable[[np.ndarray, Dict], None], 
                     max_frames: int = 0) -> bool:
        """
        Start continuous frame capture with callback.
        
        Args:
            callback: Function called for each frame: callback(frame, frame_info)
            max_frames: Maximum frames to capture (0 = unlimited)
            
        Returns:
            bool: True if capture started successfully
        """
        self._check_acquired()
        
        if not self._camera_opened:
            self.logger.error("No camera opened for capture")
            return False
        
        if self._capture_active:
            self.logger.warning("Capture already active")
            return True
        
        try:
            self._capture_active = True
            
            def capture_wrapper(frame, frame_info):
                """Wrapper to add manager-specific info and call user callback."""
                # Add manager info to frame_info
                enhanced_info = {
                    **frame_info,
                    'manager_fps': self.get_fps(),
                    'camera_id': self._current_camera_id,
                    'total_frames': self._frame_count
                }
                
                # Update manager stats
                self._update_fps_counter()
                
                # Call user callback
                callback(frame, enhanced_info)
            
            # Start capture in separate thread
            self._capture_thread = threading.Thread(
                target=self.camera_lib.capture_frames_continuous,
                args=(capture_wrapper, max_frames),
                daemon=True
            )
            self._capture_thread.start()
            
            self.logger.info(f"Continuous capture started (max_frames={max_frames})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting capture: {e}")
            self._capture_active = False
            return False
    
    def stop_capture(self) -> bool:
        """
        Stop continuous frame capture.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            if not self._capture_active:
                return True
            
            self._capture_active = False
            
            # Wait for capture thread to finish
            if self._capture_thread and self._capture_thread.is_alive():
                self._capture_thread.join(timeout=5.0)
            
            self._capture_thread = None
            self.logger.info("Continuous capture stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping capture: {e}")
            return False
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Get current camera information and status.
        
        Returns:
            Dict[str, Any]: Camera information
        """
        base_info = self.camera_lib.get_camera_info() if self._camera_opened else {}
        
        status_info = {
            'acquired': self._acquired,
            'camera_opened': self._camera_opened,
            'capture_active': self._capture_active,
            'current_camera_id': self._current_camera_id,
            'manager_fps': self.get_fps(),
            'total_frames': self._frame_count,
            'available_cameras': len(self._available_cameras)
        }
        
        return {**base_info, **status_info}
    
    def get_fps(self) -> float:
        """Get actual FPS from manager tracking."""
        return self._fps_counter
    
    def _update_fps_counter(self):
        """Update FPS tracking."""
        current_time = time.time()
        self._frame_count += 1
        
        if current_time - self._last_update_time >= 1.0:
            self._fps_counter = self._frame_count
            self._frame_count = 0
            self._last_update_time = current_time
    
    def set_camera_property(self, property_name: str, value: float) -> bool:
        """
        Set camera property (brightness, contrast, etc.).
        
        Args:
            property_name: Property name (brightness, contrast, saturation, etc.)
            value: Property value (usually 0.0 to 1.0)
            
        Returns:
            bool: True if property was set successfully
        """
        self._check_acquired()
        
        if not self._camera_opened:
            self.logger.error("No camera opened to set properties")
            return False
        
        # Map common property names to OpenCV constants
        import cv2
        property_map = {
            'brightness': cv2.CAP_PROP_BRIGHTNESS,
            'contrast': cv2.CAP_PROP_CONTRAST,
            'saturation': cv2.CAP_PROP_SATURATION,
            'hue': cv2.CAP_PROP_HUE,
            'gain': cv2.CAP_PROP_GAIN,
            'exposure': cv2.CAP_PROP_EXPOSURE,
            'white_balance': cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
            'focus': cv2.CAP_PROP_FOCUS,
        }
        
        if property_name not in property_map:
            self.logger.error(f"Unknown property: {property_name}")
            return False
        
        try:
            success = self.camera_lib.set_property(property_map[property_name], value)
            if success:
                self.logger.info(f"Set {property_name} = {value}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error setting {property_name}: {e}")
            return False
    
    def capture_frames_to_callback(self, callback, max_duration: int = 30, 
                                  frame_limit: int = 0) -> bool:
        """
        Capture frames and send to callback function (headless operation).
        
        Args:
            callback: Function to process each frame: callback(frame, frame_info)
            max_duration: Maximum duration in seconds (0 = unlimited)
            frame_limit: Maximum number of frames (0 = unlimited)
            
        Returns:
            bool: True if capture completed successfully
        """
        self._check_acquired()
        
        if not self._camera_opened:
            self.logger.error("No camera opened for frame capture")
            return False
        
        try:
            self.logger.info(f"Starting headless frame capture (max {max_duration}s)")
            
            start_time = time.time()
            frame_count = 0
            
            while True:
                # Check limits
                if max_duration > 0 and (time.time() - start_time) > max_duration:
                    break
                if frame_limit > 0 and frame_count >= frame_limit:
                    break
                
                # Capture frame
                frame = self.capture_frame()
                if frame is None:
                    continue
                
                frame_count += 1
                
                # Create frame info
                fps = self.get_fps()
                frame_info = {
                    'frame_number': frame_count,
                    'timestamp': time.time(),
                    'fps': fps,
                    'width': frame.shape[1],
                    'height': frame.shape[0],
                    'elapsed': time.time() - start_time
                }
                
                # Call user callback
                try:
                    callback(frame, frame_info)
                except Exception as e:
                    self.logger.error(f"Error in frame callback: {e}")
                    break
            
            elapsed = time.time() - start_time
            avg_fps = frame_count / elapsed if elapsed > 0 else 0
            self.logger.info(f"Frame capture completed: {frame_count} frames, {avg_fps:.1f} avg fps")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Frame capture interrupted by user")
            return True
        except Exception as e:
            self.logger.error(f"Error in frame capture: {e}")
            return False
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        if self._acquired:
            self.release()
