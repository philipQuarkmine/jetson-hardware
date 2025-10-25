"""
Display_Manager.py - Hardware-accelerated display management for Jetson Orin Nano

Manages HDMI display operations with hardware acceleration, camera integration,
and high-performance graphics rendering using the DisplayLib backend.

Author: AI Assistant  
Date: 2025-10-25
Hardware: NVIDIA Jetson Orin Nano with JetPack 6.0
Display: 1280x1024 HDMI via framebuffer /dev/fb0
"""

import os
import sys
import time
import threading
import logging
import fcntl
import subprocess
from datetime import datetime
from typing import Tuple, Optional, Union, Dict, Any
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Libs.DisplayLib import DisplayLib
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

class DisplayManager:
    """
    Hardware-accelerated display manager for Jetson Orin Nano.
    
    Provides thread-safe display operations with file locking, camera integration,
    and high-performance graphics rendering following jetson-hardware patterns.
    """
    
    _lock = threading.Lock()
    _lock_file = "/tmp/jetson_display_manager.lock"
    
    def __init__(self, framebuffer_device: str = "/dev/fb0", 
                 camera_device: str = "/dev/video0"):
        """
        Initialize Display Manager with hardware acceleration.
        
        Args:
            framebuffer_device: Path to framebuffer device (default: /dev/fb0)
            camera_device: Path to USB camera device (default: /dev/video0)
        """
        self.logger = logging.getLogger(__name__)
        self.framebuffer_device = framebuffer_device
        self.camera_device = camera_device
        
        # Initialize DisplayLib
        self.display_lib = DisplayLib(framebuffer_device)
        
        # Manager state
        self._acquired = False
        self._lock_fd = None
        self._camera_pipeline = None
        self._camera_running = False
        
        # GStreamer initialization
        Gst.init(None)
        
        # Display properties cache
        self._display_info = None
        
        # Performance tracking
        self._last_update_time = 0
        self._frame_count = 0
        self._fps_counter = 0
        
        self.logger.info(f"DisplayManager initialized - FB: {framebuffer_device}, Camera: {camera_device}")
    
    def acquire(self) -> bool:
        """
        Acquire exclusive access to display resources with file locking.
        
        Returns:
            bool: True if acquisition successful
        """
        try:
            # Thread-level lock
            DisplayManager._lock.acquire()
            
            # Process-level file lock
            self._lock_fd = open(self._lock_file, 'w')
            fcntl.lockf(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Initialize display hardware
            if not self.display_lib.initialize():
                self.logger.error("Failed to initialize display hardware")
                self.release()
                return False
            
            self._acquired = True
            self.logger.info("Display manager acquired successfully")
            
            # Cache display info
            self._display_info = self.display_lib.get_display_info()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acquire display manager: {e}")
            self.release()
            return False
    
    def release(self):
        """Release display resources and cleanup."""
        try:
            if self._camera_running:
                self.stop_camera_feed()
            
            self._acquired = False
            
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
                DisplayManager._lock.release()
            except:
                pass
                
            self.logger.info("Display manager released")
            
        except Exception as e:
            self.logger.error(f"Error releasing display manager: {e}")
    
    def _check_acquired(self):
        """Check if manager is acquired, raise exception if not."""
        if not self._acquired:
            raise RuntimeError("Must acquire DisplayManager before use")
    
    def clear_screen(self, color: Tuple[int, int, int] = None) -> bool:
        """
        Clear the display screen with specified color.
        
        Args:
            color: RGB color tuple (default: black)
            
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            success = self.display_lib.clear_display(color)
            if success:
                self._update_fps_counter()
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to clear screen: {e}")
            return False
    
    def update_display(self) -> bool:
        """
        Update display with current framebuffer content.
        
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            success = self.display_lib.update_display()
            if success:
                self._update_fps_counter()
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update display: {e}")
            return False
    
    def show_text(self, text: str, position: Tuple[int, int] = (50, 50),
                  color: Tuple[int, int, int] = None,
                  font_size: int = 24, update: bool = True) -> bool:
        """
        Display text on screen.
        
        Args:
            text: Text to display
            position: (x, y) position tuple
            color: RGB color tuple (default: white)
            font_size: Font size in pixels
            update: Whether to update display immediately
            
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            success = self.display_lib.draw_text(text, position, color, font_size)
            if success and update:
                success = self.update_display()
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to show text: {e}")
            return False
    
    def draw_rectangle(self, position: Tuple[int, int], size: Tuple[int, int],
                      color: Tuple[int, int, int] = None,
                      filled: bool = True, update: bool = True) -> bool:
        """
        Draw a rectangle on the display.
        
        Args:
            position: (x, y) top-left corner
            size: (width, height) of rectangle
            color: RGB color tuple (default: white)
            filled: True for filled rectangle, False for outline
            update: Whether to update display immediately
            
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            success = self.display_lib.draw_rectangle(position, size, color, filled)
            if success and update:
                success = self.update_display()
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to draw rectangle: {e}")
            return False
    
    def draw_circle(self, center: Tuple[int, int], radius: int,
                   color: Tuple[int, int, int] = None,
                   filled: bool = True, update: bool = True) -> bool:
        """
        Draw a circle on the display.
        
        Args:
            center: (x, y) center position
            radius: Circle radius in pixels
            color: RGB color tuple (default: white)
            filled: True for filled circle, False for outline
            update: Whether to update display immediately
            
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            success = self.display_lib.draw_circle(center, radius, color, filled)
            if success and update:
                success = self.update_display()
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to draw circle: {e}")
            return False
    
    def show_image(self, image_path: str, position: Tuple[int, int] = (0, 0),
                  scale: float = 1.0, update: bool = True) -> bool:
        """
        Display an image file on screen.
        
        Args:
            image_path: Path to image file
            position: (x, y) position to place image
            scale: Scaling factor (1.0 = original size)
            update: Whether to update display immediately
            
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            success = self.display_lib.display_image(image_path, position, scale)
            if success and update:
                success = self.update_display()
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to show image: {e}")
            return False
    
    def start_camera_feed(self, width: int = 640, height: int = 480,
                         framerate: int = 30, position: Tuple[int, int] = (0, 0)) -> bool:
        """
        Start hardware-accelerated USB camera feed display.
        
        Args:
            width: Camera capture width
            height: Camera capture height
            framerate: Capture framerate
            position: Display position (x, y)
            
        Returns:
            bool: True if camera feed started successfully
        """
        self._check_acquired()
        
        if self._camera_running:
            self.logger.warning("Camera feed already running")
            return True
        
        try:
            # Check if camera device exists
            if not os.path.exists(self.camera_device):
                self.logger.error(f"Camera device not found: {self.camera_device}")
                return False
            
            # Create GStreamer pipeline for hardware-accelerated camera
            pipeline_str = (
                f"v4l2src device={self.camera_device} ! "
                f"video/x-raw,width={width},height={height},framerate={framerate}/1 ! "
                f"nvvidconv ! "
                f"video/x-raw(memory:NVMM) ! "
                f"nvvidconv ! "
                f"video/x-raw,format=RGB ! "
                f"appsink name=sink emit-signals=true sync=false max-buffers=1 drop=true"
            )
            
            self.logger.info(f"Creating camera pipeline: {pipeline_str}")
            self._camera_pipeline = Gst.parse_launch(pipeline_str)
            
            if not self._camera_pipeline:
                self.logger.error("Failed to create GStreamer pipeline")
                return False
            
            # Get appsink element
            sink = self._camera_pipeline.get_by_name("sink")
            if not sink:
                self.logger.error("Failed to get appsink element")
                return False
            
            # Connect callback for new samples
            sink.connect("new-sample", self._on_camera_sample, position)
            
            # Start pipeline
            ret = self._camera_pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                self.logger.error("Failed to start camera pipeline")
                return False
            
            self._camera_running = True
            self.logger.info(f"Camera feed started: {width}x{height}@{framerate}fps")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start camera feed: {e}")
            return False
    
    def _on_camera_sample(self, sink, position):
        """Callback for processing camera frames."""
        try:
            sample = sink.emit("pull-sample")
            if sample:
                buf = sample.get_buffer()
                caps = sample.get_caps()
                
                # Extract frame data and update display
                # This is a simplified version - full implementation would
                # convert GStreamer buffer to PIL image and composite it
                self._update_fps_counter()
                
        except Exception as e:
            self.logger.error(f"Error processing camera sample: {e}")
        
        return Gst.FlowReturn.OK
    
    def stop_camera_feed(self) -> bool:
        """
        Stop camera feed and cleanup resources.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            if self._camera_pipeline:
                self._camera_pipeline.set_state(Gst.State.NULL)
                self._camera_pipeline = None
            
            self._camera_running = False
            self.logger.info("Camera feed stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop camera feed: {e}")
            return False
    
    def get_display_info(self) -> Dict[str, Any]:
        """
        Get display capabilities and current status.
        
        Returns:
            dict: Display information
        """
        base_info = self.display_lib.get_display_info() if self._display_info else {}
        
        status_info = {
            'acquired': self._acquired,
            'camera_running': self._camera_running,
            'camera_device': self.camera_device,
            'fps': self._fps_counter,
            'frame_count': self._frame_count,
            'last_update': self._last_update_time
        }
        
        return {**base_info, **status_info}
    
    def _update_fps_counter(self):
        """Update FPS tracking."""
        current_time = time.time()
        self._frame_count += 1
        
        if current_time - self._last_update_time >= 1.0:
            self._fps_counter = self._frame_count
            self._frame_count = 0
            self._last_update_time = current_time
    
    def show_system_info(self, update: bool = True) -> bool:
        """
        Display system information on screen.
        
        Args:
            update: Whether to update display immediately
            
        Returns:
            bool: True if successful
        """
        self._check_acquired()
        
        try:
            # Clear screen first
            self.clear_screen((0, 20, 40))  # Dark blue background
            
            # Get system info
            info = self.get_display_info()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Display header
            self.show_text("JETSON ORIN NANO - DISPLAY SYSTEM", (50, 30), 
                          (255, 255, 0), 32, False)  # Yellow header
            
            # Display info
            y_pos = 100
            line_height = 30
            
            info_lines = [
                f"Time: {current_time}",
                f"Resolution: {info.get('width', 0)}x{info.get('height', 0)}",
                f"Color Depth: {info.get('bits_per_pixel', 0)} bits per pixel",
                f"FPS: {info.get('fps', 0)}",
                f"Frame Count: {info.get('frame_count', 0)}",
                f"Camera: {'Running' if info.get('camera_running', False) else 'Stopped'}",
                f"Camera Device: {info.get('camera_device', 'N/A')}",
                f"Status: {'ACQUIRED' if info.get('acquired', False) else 'NOT ACQUIRED'}"
            ]
            
            for line in info_lines:
                self.show_text(line, (50, y_pos), (255, 255, 255), 20, False)
                y_pos += line_height
            
            # Draw status indicator
            status_color = (0, 255, 0) if info.get('acquired', False) else (255, 0, 0)
            self.draw_circle((info.get('width', 1280) - 50, 50), 20, status_color, True, False)
            
            if update:
                return self.update_display()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to show system info: {e}")
            return False
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        if self._acquired:
            self.release()