"""
DisplayLib.py - Hardware-accelerated display management library for Jetson Orin Nano

This library provides direct framebuffer access with PIL integration for high-performance
graphics operations on the HDMI display. Optimized for 1280x1024x32 resolution with
hardware acceleration support.

Author: AI Assistant
Date: 2025-10-25
Hardware: NVIDIA Jetson Orin Nano with JetPack 6.0
Display: 1280x1024 HDMI via framebuffer /dev/fb0
"""

import fcntl
import logging
import mmap
import os
import struct
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Framebuffer constants for ioctl operations
FBIOGET_VSCREENINFO = 0x4600
FBIOGET_FSCREENINFO = 0x4602


class FramebufferInfo:
    """Container for framebuffer information"""

    def __init__(self):
        self.width = 0
        self.height = 0
        self.bits_per_pixel = 0
        self.bytes_per_pixel = 0
        self.line_length = 0
        self.buffer_size = 0


class DisplayLib:
    """
    Hardware-accelerated display library for Jetson framebuffer access.

    Provides efficient PIL-based graphics operations with direct framebuffer
    memory mapping for optimal performance on NVIDIA Jetson hardware.
    """

    def __init__(self, framebuffer_device: str = "/dev/fb0"):
        """
        Initialize display library with framebuffer access.

        Args:
            framebuffer_device: Path to framebuffer device (default: /dev/fb0)
        """
        self.logger = logging.getLogger(__name__)
        self.framebuffer_device = framebuffer_device
        self.fb_fd = None
        self.fb_mmap = None
        self.fb_info = FramebufferInfo()
        self.current_image = None
        self._is_initialized = False

        # Color format constants
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.CYAN = (0, 255, 255)
        self.MAGENTA = (255, 0, 255)

        self.logger.info(f"DisplayLib initialized for {framebuffer_device}")

    def initialize(self) -> bool:
        """
        Initialize framebuffer access and memory mapping.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Open framebuffer device
            self.fb_fd = os.open(self.framebuffer_device, os.O_RDWR)
            self.logger.info(f"Opened framebuffer device: {self.framebuffer_device}")

            # Get framebuffer information
            if not self._get_framebuffer_info():
                return False

            # Create memory mapping
            self.fb_mmap = mmap.mmap(
                self.fb_fd,
                self.fb_info.buffer_size,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
            )

            # Create PIL image for drawing operations
            self.current_image = Image.new(
                "RGB", (self.fb_info.width, self.fb_info.height), self.BLACK
            )

            self._is_initialized = True
            self.logger.info(
                f"Display initialized: {self.fb_info.width}x{self.fb_info.height}x{self.fb_info.bits_per_pixel}bpp"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            self._cleanup()
            return False

    def _get_framebuffer_info(self) -> bool:
        """
        Retrieve framebuffer information using ioctl calls.

        Returns:
            bool: True if info retrieved successfully
        """
        try:
            # CRITICAL FIX: Read actual hardware parameters from sysfs
            # This is more reliable than ioctl on some Jetson framebuffers
            try:
                with open("/sys/class/graphics/fb0/virtual_size") as f:
                    size_str = f.read().strip()
                    width_str, height_str = size_str.split(",")
                    self.fb_info.width = int(width_str)
                    self.fb_info.height = int(height_str)

                with open("/sys/class/graphics/fb0/stride") as f:
                    self.fb_info.line_length = int(f.read().strip())

                with open("/sys/class/graphics/fb0/bits_per_pixel") as f:
                    self.fb_info.bits_per_pixel = int(f.read().strip())

                self.fb_info.bytes_per_pixel = self.fb_info.bits_per_pixel // 8
                self.fb_info.buffer_size = self.fb_info.line_length * self.fb_info.height

                self.logger.info(
                    f"Hardware framebuffer: {self.fb_info.width}x{self.fb_info.height}, "
                    f"stride={self.fb_info.line_length}, {self.fb_info.bits_per_pixel}bpp"
                )

            except Exception as sysfs_error:
                self.logger.warning(f"Failed to read sysfs framebuffer info: {sysfs_error}")

                # Fallback to ioctl method
                import struct

                # Get variable screen info - using correct struct format
                vinfo_fmt = "32I"  # 32 unsigned integers for fb_var_screeninfo
                vinfo_buf = struct.pack(vinfo_fmt, *([0] * 32))
                vinfo_result = fcntl.ioctl(self.fb_fd, FBIOGET_VSCREENINFO, vinfo_buf)
                vinfo = struct.unpack(vinfo_fmt, vinfo_result)

                self.fb_info.width = vinfo[0]
                self.fb_info.height = vinfo[1]
                self.fb_info.bits_per_pixel = vinfo[6]
                self.fb_info.bytes_per_pixel = self.fb_info.bits_per_pixel // 8

                # Get fixed screen info - using correct struct format for line_length
                finfo_fmt = "16s 2I 16s 8I"  # Simplified struct fb_fix_screeninfo
                finfo_buf = struct.pack(finfo_fmt, b"", 0, 0, b"", 0, 0, 0, 0, 0, 0, 0, 0)
                finfo_result = fcntl.ioctl(self.fb_fd, FBIOGET_FSCREENINFO, finfo_buf)
                finfo = struct.unpack(finfo_fmt, finfo_result)

                # line_length should be at index 4 in the unpacked data
                self.fb_info.line_length = finfo[4]

                # If line_length is still 0, calculate it manually
                if self.fb_info.line_length == 0:
                    self.fb_info.line_length = self.fb_info.width * self.fb_info.bytes_per_pixel
                    self.logger.warning(
                        f"Calculated line_length manually: {self.fb_info.line_length}"
                    )

                self.fb_info.buffer_size = self.fb_info.line_length * self.fb_info.height

            self.logger.info(
                f"Framebuffer: {self.fb_info.width}x{self.fb_info.height}, "
                f"{self.fb_info.bits_per_pixel}bpp, line_length={self.fb_info.line_length}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to get framebuffer info: {e}")
            # Fallback to reasonable defaults for simple framebuffer
            try:
                self.fb_info.width = 1280
                self.fb_info.height = 1024
                self.fb_info.bits_per_pixel = 32
                self.fb_info.bytes_per_pixel = 4
                self.fb_info.line_length = self.fb_info.width * self.fb_info.bytes_per_pixel
                self.fb_info.buffer_size = self.fb_info.line_length * self.fb_info.height
                self.logger.warning(
                    f"Using fallback framebuffer settings: {self.fb_info.width}x{self.fb_info.height}"
                )
                return True
            except:
                return False

    def clear_display(self, color: Tuple[int, int, int] = None) -> bool:
        """
        Clear the entire display with specified color.

        Args:
            color: RGB color tuple (default: black)

        Returns:
            bool: True if successful
        """
        if not self._is_initialized:
            self.logger.error("Display not initialized")
            return False

        try:
            if color is None:
                color = self.BLACK

            # Clear PIL image
            self.current_image = Image.new("RGB", (self.fb_info.width, self.fb_info.height), color)

            # Update framebuffer
            return self.update_display()

        except Exception as e:
            self.logger.error(f"Failed to clear display: {e}")
            return False

    def update_display(self) -> bool:
        """
        Update framebuffer with current PIL image content.

        Returns:
            bool: True if successful
        """
        if not self._is_initialized or self.current_image is None:
            self.logger.error("Display not initialized or no image")
            return False

        try:
            # Convert PIL image to framebuffer format (BGR for most framebuffers)
            if self.current_image.mode != "RGB":
                rgb_image = self.current_image.convert("RGB")
            else:
                rgb_image = self.current_image

            # Get raw pixel data
            pixels = np.array(rgb_image)

            # CRITICAL FIX: Handle stride properly for correct horizontal alignment
            # Create framebuffer-aligned array with proper line_length
            fb_height = self.fb_info.height
            fb_line_length = self.fb_info.line_length
            fb_bytes_per_pixel = self.fb_info.bytes_per_pixel
            fb_width_pixels = fb_line_length // fb_bytes_per_pixel

            # Create properly sized framebuffer array
            fb_array = np.zeros((fb_height, fb_width_pixels, fb_bytes_per_pixel), dtype=np.uint8)

            # Copy image data to framebuffer array (handle potential size differences)
            copy_height = min(pixels.shape[0], fb_height)
            copy_width = min(pixels.shape[1], self.fb_info.width)

            if fb_bytes_per_pixel == 4:
                # BGRA format - need to swap red and blue channels
                fb_array[:copy_height, :copy_width, 0] = pixels[
                    :copy_height, :copy_width, 2
                ]  # B <- R
                fb_array[:copy_height, :copy_width, 1] = pixels[
                    :copy_height, :copy_width, 1
                ]  # G <- G
                fb_array[:copy_height, :copy_width, 2] = pixels[
                    :copy_height, :copy_width, 0
                ]  # R <- B
                fb_array[:copy_height, :copy_width, 3] = 255  # A
            else:
                # BGR format - need to swap red and blue channels
                fb_array[:copy_height, :copy_width, 0] = pixels[
                    :copy_height, :copy_width, 2
                ]  # B <- R
                fb_array[:copy_height, :copy_width, 1] = pixels[
                    :copy_height, :copy_width, 1
                ]  # G <- G
                fb_array[:copy_height, :copy_width, 2] = pixels[
                    :copy_height, :copy_width, 0
                ]  # R <- B

            # Write to framebuffer with proper stride
            self.fb_mmap.seek(0)
            self.fb_mmap.write(fb_array.tobytes())
            self.fb_mmap.flush()

            return True

        except Exception as e:
            self.logger.error(f"Failed to update display: {e}")
            return False

    def draw_text(
        self,
        text: str,
        position: Tuple[int, int],
        color: Tuple[int, int, int] = None,
        font_size: int = 24,
    ) -> bool:
        """
        Draw text on the display at specified position.

        Args:
            text: Text to draw
            position: (x, y) position tuple
            color: RGB color tuple (default: white)
            font_size: Font size in pixels

        Returns:
            bool: True if successful
        """
        if not self._is_initialized:
            self.logger.error("Display not initialized")
            return False

        try:
            if color is None:
                color = self.WHITE

            draw = ImageDraw.Draw(self.current_image)

            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
                )
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None

            draw.text(position, text, fill=color, font=font)
            return True

        except Exception as e:
            self.logger.error(f"Failed to draw text: {e}")
            return False

    def draw_rectangle(
        self,
        position: Tuple[int, int],
        size: Tuple[int, int],
        color: Tuple[int, int, int] = None,
        fill: bool = True,
    ) -> bool:
        """
        Draw a rectangle on the display.

        Args:
            position: (x, y) top-left corner
            size: (width, height) of rectangle
            color: RGB color tuple (default: white)
            fill: True for filled rectangle, False for outline

        Returns:
            bool: True if successful
        """
        if not self._is_initialized:
            self.logger.error("Display not initialized")
            return False

        try:
            if color is None:
                color = self.WHITE

            draw = ImageDraw.Draw(self.current_image)
            x, y = position
            width, height = size

            if fill:
                draw.rectangle([x, y, x + width, y + height], fill=color)
            else:
                draw.rectangle([x, y, x + width, y + height], outline=color)

            return True

        except Exception as e:
            self.logger.error(f"Failed to draw rectangle: {e}")
            return False

    def draw_circle(
        self,
        center: Tuple[int, int],
        radius: int,
        color: Tuple[int, int, int] = None,
        fill: bool = True,
    ) -> bool:
        """
        Draw a circle on the display.

        Args:
            center: (x, y) center position
            radius: Circle radius in pixels
            color: RGB color tuple (default: white)
            fill: True for filled circle, False for outline

        Returns:
            bool: True if successful
        """
        if not self._is_initialized:
            self.logger.error("Display not initialized")
            return False

        try:
            if color is None:
                color = self.WHITE

            draw = ImageDraw.Draw(self.current_image)
            x, y = center

            if fill:
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
            else:
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=color)

            return True

        except Exception as e:
            self.logger.error(f"Failed to draw circle: {e}")
            return False

    def display_image(
        self, image_path: str, position: Tuple[int, int] = (0, 0), scale: float = 1.0
    ) -> bool:
        """
        Display an image file on the screen.

        Args:
            image_path: Path to image file
            position: (x, y) position to place image
            scale: Scaling factor (1.0 = original size)

        Returns:
            bool: True if successful
        """
        if not self._is_initialized:
            self.logger.error("Display not initialized")
            return False

        try:
            # Load image
            img = Image.open(image_path)

            # Scale if necessary
            if scale != 1.0:
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.LANCZOS)

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Paste onto current image
            self.current_image.paste(img, position)

            return True

        except Exception as e:
            self.logger.error(f"Failed to display image: {e}")
            return False

    def get_display_info(self) -> dict:
        """
        Get display information and capabilities.

        Returns:
            dict: Display information
        """
        return {
            "width": self.fb_info.width,
            "height": self.fb_info.height,
            "bits_per_pixel": self.fb_info.bits_per_pixel,
            "bytes_per_pixel": self.fb_info.bytes_per_pixel,
            "line_length": self.fb_info.line_length,
            "buffer_size": self.fb_info.buffer_size,
            "initialized": self._is_initialized,
            "framebuffer_device": self.framebuffer_device,
        }

    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.fb_mmap:
                self.fb_mmap.close()
                self.fb_mmap = None

            if self.fb_fd is not None:
                os.close(self.fb_fd)
                self.fb_fd = None

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor - cleanup resources."""
        self._cleanup()
