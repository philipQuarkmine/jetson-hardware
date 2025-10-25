#!/usr/bin/env python3
"""
CameraLib.py

Low-level camera interface library for Jetson Orin Nano camera management.
Provides unified interface for USB cameras and future CSI camera support.

Author: AI Assistant
Date: 2025-10-25
Hardware: NVIDIA Jetson Orin Nano with JetPack 6.0
Cameras: USB 2.0 Camera, Future IMX708 CSI support
"""

import logging
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np


class CameraType(Enum):
    """Camera backend types."""
    USB = "usb"
    CSI = "csi"  # Future IMX708 support
    GSTREAMER = "gstreamer"


class CameraResolution(Enum):
    """Standard camera resolutions."""
    QVGA = (320, 240)
    VGA = (640, 480)
    HD = (1280, 720)
    FHD = (1920, 1080)
    UHD = (3840, 2160)


class CameraFormat(Enum):
    """Camera pixel formats."""
    YUYV = "YUYV"
    MJPG = "MJPG"
    RGB24 = "RGB24"
    BGR24 = "BGR24"


class CameraInfo:
    """Camera device information."""
    
    def __init__(self, device_id: int, name: str, camera_type: CameraType,
                 supported_resolutions: List[Tuple[int, int]] = None,
                 supported_formats: List[str] = None):
        self.device_id = device_id
        self.name = name
        self.camera_type = camera_type
        self.supported_resolutions = supported_resolutions or []
        self.supported_formats = supported_formats or []
        self.is_available = True


class CameraLib:
    """
    Low-level camera interface for Jetson Orin Nano.
    
    Provides unified access to USB cameras with future support for CSI cameras.
    Optimized for robotics applications with real-time performance.
    """
    
    def __init__(self):
        """Initialize camera library."""
        self.logger = logging.getLogger(__name__)
        self._capture = None
        self._is_opened = False
        self._current_camera = None
        self._frame_lock = threading.Lock()
        self._last_frame = None
        self._frame_count = 0
        self._fps_start_time = time.time()
        
        # Camera configuration
        self._width = 640
        self._height = 480
        self._fps = 30
        self._format = CameraFormat.BGR24
        
    def discover_cameras(self) -> List[CameraInfo]:
        """
        Discover available cameras on the system.
        
        Returns:
            List[CameraInfo]: Available camera devices
        """
        cameras = []
        
        # Check USB cameras (OpenCV backend)
        for device_id in range(4):  # Check first 4 video devices
            device_path = f"/dev/video{device_id}"
            if Path(device_path).exists():
                try:
                    # Test if camera can be opened
                    test_cap = cv2.VideoCapture(device_id)
                    if test_cap.isOpened():
                        # Try to read camera name from v4l2
                        camera_name = self._get_camera_name(device_id)
                        
                        # Get supported resolutions
                        resolutions = self._probe_resolutions(test_cap)
                        
                        camera_info = CameraInfo(
                            device_id=device_id,
                            name=camera_name,
                            camera_type=CameraType.USB,
                            supported_resolutions=resolutions,
                            supported_formats=["BGR24", "YUYV"]
                        )
                        cameras.append(camera_info)
                        self.logger.info(f"Found USB camera: {camera_name} on /dev/video{device_id}")
                    
                    test_cap.release()
                except Exception as e:
                    self.logger.debug(f"Could not probe camera {device_id}: {e}")
        
        # Future: Add CSI camera discovery for IMX708
        # This would use GStreamer or libcamera for CSI cameras
        
        return cameras
    
    def _get_camera_name(self, device_id: int) -> str:
        """Get camera name from v4l2 info."""
        try:
            import subprocess
            result = subprocess.run(['v4l2-ctl', '--device', f'/dev/video{device_id}', 
                                   '--info'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Card type' in line:
                        return line.split(':')[1].strip()
        except:
            pass
        return f"USB Camera {device_id}"
    
    def _probe_resolutions(self, capture: cv2.VideoCapture) -> List[Tuple[int, int]]:
        """Probe supported resolutions for a camera."""
        common_resolutions = [
            (320, 240), (640, 480), (800, 600), (1024, 768),
            (1280, 720), (1280, 960), (1600, 1200), (1920, 1080)
        ]
        
        supported = []
        original_width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        original_height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        for width, height in common_resolutions:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            if abs(actual_width - width) < 10 and abs(actual_height - height) < 10:
                supported.append((int(actual_width), int(actual_height)))
        
        # Restore original resolution
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, original_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, original_height)
        
        return supported
    
    def open_camera(self, camera_id: int, width: int = 640, height: int = 480, 
                   fps: int = 30) -> bool:
        """
        Open camera for capture.
        
        Args:
            camera_id: Camera device ID (usually 0 for first USB camera)
            width: Capture width in pixels
            height: Capture height in pixels
            fps: Desired framerate
            
        Returns:
            bool: True if camera opened successfully
        """
        try:
            if self._is_opened:
                self.logger.warning("Camera already opened, closing previous connection")
                self.close_camera()
            
            self.logger.info(f"Opening camera {camera_id} at {width}x{height}@{fps}fps")
            
            # Create VideoCapture object
            self._capture = cv2.VideoCapture(camera_id)
            
            if not self._capture.isOpened():
                self.logger.error(f"Failed to open camera {camera_id}")
                return False
            
            # Configure camera properties
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self._capture.set(cv2.CAP_PROP_FPS, fps)
            
            # Verify actual settings
            actual_width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self._capture.get(cv2.CAP_PROP_FPS)
            
            self._width = actual_width
            self._height = actual_height
            self._fps = actual_fps
            self._current_camera = camera_id
            self._is_opened = True
            
            # Reset frame counting
            self._frame_count = 0
            self._fps_start_time = time.time()
            
            self.logger.info(f"Camera opened: {actual_width}x{actual_height}@{actual_fps:.1f}fps")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening camera {camera_id}: {e}")
            return False
    
    def close_camera(self) -> bool:
        """
        Close camera and release resources.
        
        Returns:
            bool: True if closed successfully
        """
        try:
            if self._capture:
                self._capture.release()
                self._capture = None
            
            self._is_opened = False
            self._current_camera = None
            self._last_frame = None
            
            self.logger.info("Camera closed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing camera: {e}")
            return False
    
    def capture_frame(self) -> np.ndarray | None:
        """
        Capture a single frame from the camera.
        
        Returns:
            Optional[np.ndarray]: BGR image frame, None if capture failed
        """
        if not self._is_opened or not self._capture:
            self.logger.error("Camera not opened")
            return None
        
        try:
            with self._frame_lock:
                ret, frame = self._capture.read()
                
                if not ret or frame is None:
                    self.logger.warning("Failed to capture frame")
                    return None
                
                # Update frame statistics
                self._frame_count += 1
                self._last_frame = frame.copy()
                
                return frame
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def capture_frames_continuous(self, callback, max_frames: int = 0) -> bool:
        """
        Continuously capture frames and call callback function.
        
        Args:
            callback: Function to call with each frame callback(frame, frame_info)
            max_frames: Maximum frames to capture (0 = unlimited)
            
        Returns:
            bool: True if started successfully
        """
        if not self._is_opened:
            self.logger.error("Camera not opened for continuous capture")
            return False
        
        try:
            frame_count = 0
            start_time = time.time()
            
            while max_frames == 0 or frame_count < max_frames:
                frame = self.capture_frame()
                if frame is None:
                    continue
                
                # Frame information
                frame_info = {
                    'frame_number': frame_count,
                    'timestamp': time.time(),
                    'width': frame.shape[1],
                    'height': frame.shape[0],
                    'fps': self.get_actual_fps()
                }
                
                # Call user callback
                try:
                    callback(frame, frame_info)
                except Exception as e:
                    self.logger.error(f"Error in frame callback: {e}")
                    break
                
                frame_count += 1
            
            elapsed = time.time() - start_time
            avg_fps = frame_count / elapsed if elapsed > 0 else 0
            self.logger.info(f"Continuous capture completed: {frame_count} frames, {avg_fps:.1f} avg fps")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Continuous capture interrupted by user")
            return True
        except Exception as e:
            self.logger.error(f"Error in continuous capture: {e}")
            return False
    
    def save_image(self, filename: str, frame: np.ndarray | None = None) -> bool:
        """
        Save current frame or provided frame to file.
        
        Args:
            filename: Output filename (supports .jpg, .png, .bmp)
            frame: Frame to save (None = capture new frame)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            if frame is None:
                frame = self.capture_frame()
                
            if frame is None:
                self.logger.error("No frame available to save")
                return False
            
            success = cv2.imwrite(filename, frame)
            if success:
                self.logger.info(f"Image saved to {filename}")
                return True
            else:
                self.logger.error(f"Failed to save image to {filename}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving image {filename}: {e}")
            return False
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Get current camera information and status.
        
        Returns:
            Dict[str, Any]: Camera information
        """
        if not self._is_opened:
            return {'status': 'closed', 'camera_id': None}
        
        return {
            'status': 'opened',
            'camera_id': self._current_camera,
            'width': self._width,
            'height': self._height,
            'fps': self._fps,
            'actual_fps': self.get_actual_fps(),
            'frame_count': self._frame_count,
            'format': self._format.value
        }
    
    def get_actual_fps(self) -> float:
        """Calculate actual FPS based on frame count."""
        elapsed = time.time() - self._fps_start_time
        if elapsed > 0 and self._frame_count > 0:
            return self._frame_count / elapsed
        return 0.0
    
    def is_opened(self) -> bool:
        """Check if camera is currently opened."""
        return self._is_opened and self._capture is not None
    
    def set_property(self, property_id: int, value: float) -> bool:
        """
        Set camera property (brightness, contrast, etc.).
        
        Args:
            property_id: OpenCV property ID (e.g., cv2.CAP_PROP_BRIGHTNESS)
            value: Property value
            
        Returns:
            bool: True if property was set successfully
        """
        if not self._is_opened or not self._capture:
            return False
        
        try:
            success = self._capture.set(property_id, value)
            if success:
                self.logger.debug(f"Set camera property {property_id} = {value}")
            return success
        except Exception as e:
            self.logger.error(f"Error setting camera property {property_id}: {e}")
            return False
    
    def get_property(self, property_id: int) -> float | None:
        """
        Get camera property value.
        
        Args:
            property_id: OpenCV property ID
            
        Returns:
            Optional[float]: Property value, None if failed
        """
        if not self._is_opened or not self._capture:
            return None
        
        try:
            value = self._capture.get(property_id)
            return value
        except Exception as e:
            self.logger.error(f"Error getting camera property {property_id}: {e}")
            return None
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        if self._is_opened:
            self.close_camera()
