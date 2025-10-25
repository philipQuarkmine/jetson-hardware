#!/usr/bin/env python3
"""
jetson_screensaver.py

Gentle wave screensaver for Jetson Orin Nano display.
Creates soothing color waves across the framebuffer display.

Usage:
    python3 SimpleTests/jetson_screensaver.py
    
Controls:
    - Ctrl+C to exit
    - Automatically dims and cycles through peaceful colors
"""

import math
import signal
import sys
import time
from typing import Tuple

sys.path.append('/home/phiip/workspace/jetson-hardware')

import numpy as np

from Managers.Display_Manager import DisplayManager


class JetsonScreensaver:
    """
    Peaceful wave screensaver for Jetson display.
    
    Features:
    - Gentle sine wave patterns
    - Slow color transitions
    - Low brightness for ambient lighting
    - Smooth animations optimized for framebuffer
    """
    
    def __init__(self):
        self.display = DisplayManager()
        self.running = False
        self.start_time = time.time()
        
        # Wave parameters - more dramatic and slower
        self.wave_speed = 0.3  # Much slower, very peaceful movement
        self.wave_amplitude = 150  # Much taller waves - more dramatic
        self.color_cycle_speed = 0.05  # Even slower color changes
        
        # Display properties (will be updated when display is acquired)
        self.width = 1280
        self.height = 1024
        
        # Trailing edge tracking for smooth animation
        self.prev_wave_points = []
        self.prev_sparkles = []
        self.prev_base_color = (0, 0, 0)
        
        # Enhanced color palettes - more distinct and visible transitions
        self.color_palettes = [
            # Deep ocean blues
            [(25, 40, 80), (45, 70, 120), (35, 55, 100)],
            # Emerald greens  
            [(40, 70, 40), (60, 100, 60), (50, 85, 50)],
            # Sunset purples
            [(70, 40, 80), (90, 50, 100), (80, 45, 90)],
            # Warm amber golds
            [(80, 60, 30), (100, 80, 40), (90, 70, 35)],
            # Twilight teals
            [(30, 60, 70), (40, 80, 90), (35, 70, 80)],
            # Rose quartz
            [(70, 50, 60), (90, 60, 80), (80, 55, 70)],
            # Lavender mist
            [(60, 50, 80), (80, 70, 100), (70, 60, 90)]
        ]
        
    def setup_signal_handlers(self):
        """Setup graceful exit on Ctrl+C."""
        def signal_handler(signum, frame):
            print("\n🌙 Screensaver stopping gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def get_current_colors(self, t: float) -> Tuple[int, int, int]:
        """
        Get current color based on time for smooth transitions.
        
        Args:
            t: Current time in seconds
            
        Returns:
            Tuple[int, int, int]: RGB color values
        """
        # Cycle through color palettes extremely slowly - 2+ minutes per palette
        palette_index = int((t * self.color_cycle_speed) % len(self.color_palettes))
        palette = self.color_palettes[palette_index]
        
        # Blend between colors in the palette - slower transitions within palette
        blend_t = (t * self.color_cycle_speed * 2) % 1.0  # Slower color blending
        
        if blend_t < 0.33:
            # Blend between color 0 and 1
            mix = blend_t * 3
            color1, color2 = palette[0], palette[1]
        elif blend_t < 0.67:
            # Blend between color 1 and 2
            mix = (blend_t - 0.33) * 3
            color1, color2 = palette[1], palette[2]
        else:
            # Blend between color 2 and 0
            mix = (blend_t - 0.67) * 3
            color1, color2 = palette[2], palette[0]
        
        # Linear interpolation between colors
        r = int(color1[0] * (1 - mix) + color2[0] * mix)
        g = int(color1[1] * (1 - mix) + color2[1] * mix)
        b = int(color1[2] * (1 - mix) + color2[2] * mix)
        
        return (r, g, b)
    
    def create_wave_pattern(self, t: float) -> list:
        """
        Create wave pattern coordinates for current time.
        
        Args:
            t: Current time in seconds
            
        Returns:
            list: List of (x, y) points defining the wave
        """
        points = []
        
        # Create multiple overlapping waves for richness
        for x in range(0, self.width, 6):  # Sample every 6 pixels for smoother curves
            # Primary wave
            y1 = math.sin((x * 0.005) + (t * self.wave_speed)) * self.wave_amplitude
            
            # Secondary wave (different frequency)
            y2 = math.sin((x * 0.003) + (t * self.wave_speed * 0.7)) * (self.wave_amplitude * 0.6)
            
            # Tertiary wave (very slow, adds depth)
            y3 = math.sin((x * 0.001) + (t * self.wave_speed * 0.3)) * (self.wave_amplitude * 0.4)
            
            # Combine waves and center on screen
            y = (self.height // 2) + int(y1 + y2 + y3)
            
            # Keep within screen bounds
            y = max(0, min(self.height - 1, y))
            
            points.append((x, y))
        
        return points
    
    def draw_wave_frame(self, t: float):
        """
        Draw a single frame using trailing edge technique.
        Only erase old positions and draw new ones.
        
        Args:
            t: Current time in seconds
        """
        try:
            # Get current colors and wave data
            base_color = self.get_current_colors(t)
            bg_color = (base_color[0] // 5, base_color[1] // 5, base_color[2] // 5)
            current_wave_points = self.create_wave_pattern(t)
            
            # Calculate current sparkles - much slower and more peaceful
            sparkle_t = t * 0.2  # Much slower sparkle movement
            current_sparkles = []
            for i in range(3):  # Keep 3 sparkles for gentle ambiance
                sparkle_x = int((math.sin(sparkle_t * 0.08 + i) * 0.5 + 0.5) * self.width)
                sparkle_y = int((math.sin(sparkle_t * 0.1 + i * 2) * 0.5 + 0.5) * self.height)
                current_sparkles.append((sparkle_x, sparkle_y))
            
            # STEP 1: Erase trailing edges (old positions)
            if self.prev_wave_points:
                # Erase old wave segments with background color
                center_y = self.height // 2
                for i in range(len(self.prev_wave_points) - 1):
                    x1, y1 = self.prev_wave_points[i]
                    x2, y2 = self.prev_wave_points[i + 1]
                    segment_width = max(1, x2 - x1)
                    
                    # Erase old wave area
                    if y1 < center_y:
                        height = center_y - y1
                        if height > 2:
                            self.display.draw_rectangle((x1, y1), (segment_width, height), 
                                                      bg_color, True, False)
                    else:
                        height = y1 - center_y  
                        if height > 2:
                            self.display.draw_rectangle((x1, center_y), (segment_width, height), 
                                                      bg_color, True, False)
            
            # Erase old sparkles
            for sparkle_x, sparkle_y in self.prev_sparkles:
                self.display.draw_circle((sparkle_x, sparkle_y), 4, bg_color, True, False)
            
            # STEP 2: Draw leading edges (new positions) 
            center_y = self.height // 2
            for i in range(len(current_wave_points) - 1):
                x1, y1 = current_wave_points[i]
                x2, y2 = current_wave_points[i + 1]
                segment_width = max(1, x2 - x1)
                
                # Draw new wave area
                if y1 < center_y:
                    height = center_y - y1
                    if height > 2:
                        self.display.draw_rectangle((x1, y1), (segment_width, height), 
                                                  base_color, True, False)
                else:
                    height = y1 - center_y
                    if height > 2:
                        self.display.draw_rectangle((x1, center_y), (segment_width, height), 
                                                  base_color, True, False)
            
            # Draw new sparkles
            sparkle_color = (
                min(255, base_color[0] + 25),
                min(255, base_color[1] + 25), 
                min(255, base_color[2] + 25)
            )
            for sparkle_x, sparkle_y in current_sparkles:
                self.display.draw_circle((sparkle_x, sparkle_y), 3, sparkle_color, True, False)
            
            # STEP 3: Store current positions for next frame's trailing edge
            self.prev_wave_points = current_wave_points.copy()
            self.prev_sparkles = current_sparkles.copy()
            self.prev_base_color = base_color
            
            # Update display
            self.display.update_display()
            
        except Exception as e:
            print(f"Error drawing frame: {e}")
    
    def show_startup_message(self):
        """Show a gentle startup message."""
        self.display.clear_screen((20, 20, 40))
        
        # Title
        self.display.show_text("JETSON SCREENSAVER", (400, 300), (100, 150, 200), 48, False)
        
        # Subtitle
        self.display.show_text("Peaceful Waves", (500, 380), (80, 120, 160), 24, False)
        
        # Instructions
        self.display.show_text("Press Ctrl+C to exit", (520, 450), (60, 100, 140), 16, False)
        
        # Show startup for 3 seconds
        self.display.update_display()
        time.sleep(3)
    
    def show_stats(self, runtime: float, fps: float):
        """
        Show runtime statistics in corner.
        
        Args:
            runtime: Total runtime in seconds
            fps: Current FPS
        """
        # Format runtime
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        seconds = int(runtime % 60)
        
        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Show in bottom right corner (dim)
        stats_color = (40, 60, 80)
        self.display.show_text(f"Runtime: {time_str}", (self.width - 200, self.height - 50), 
                              stats_color, 14, False)
        self.display.show_text(f"FPS: {fps:.1f}", (self.width - 200, self.height - 30), 
                              stats_color, 14, False)
    
    def run(self):
        """Run the screensaver main loop."""
        print("🌙 Starting Jetson Screensaver...")
        
        # Acquire display
        if not self.display.acquire():
            print("❌ Failed to acquire display manager")
            return False
        
        try:
            # Get actual display dimensions
            info = self.display.get_display_info()
            self.width = info.get('width', 1280)
            self.height = info.get('height', 1024)
            
            print(f"📺 Display: {self.width}x{self.height}")
            print("🎨 Starting peaceful wave animation...")
            print("⌨️  Press Ctrl+C to exit")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Show startup message
            self.show_startup_message()
            
            # Initialize screen with base background for trailing edge technique
            base_color = self.get_current_colors(0)
            bg_color = (base_color[0] // 5, base_color[1] // 5, base_color[2] // 5)
            self.display.clear_screen(bg_color)
            
            # Main animation loop
            self.running = True
            frame_count = 0
            fps_start_time = time.time()
            
            while self.running:
                frame_start = time.time()
                
                # Current animation time
                t = time.time() - self.start_time
                
                # Draw wave frame
                self.draw_wave_frame(t)
                
                # Show stats every 60 frames (about once per second)
                if frame_count % 60 == 0:
                    runtime = time.time() - self.start_time
                    fps = frame_count / (time.time() - fps_start_time) if frame_count > 0 else 0
                    self.show_stats(runtime, fps)
                
                frame_count += 1
                
                # Target ~12 FPS for smooth display without flicker
                frame_time = time.time() - frame_start
                target_frame_time = 1.0 / 12.0  # 12 FPS - reduce flicker
                
                if frame_time < target_frame_time:
                    time.sleep(target_frame_time - frame_time)
            
            # Graceful shutdown
            runtime = time.time() - self.start_time
            avg_fps = frame_count / runtime if runtime > 0 else 0
            
            print(f"\n✅ Screensaver completed")
            print(f"   Runtime: {runtime:.1f} seconds")
            print(f"   Frames: {frame_count}")
            print(f"   Average FPS: {avg_fps:.1f}")
            
            # Show goodbye message
            self.display.clear_screen((30, 20, 40))
            self.display.show_text("SCREENSAVER STOPPED", (400, 400), (150, 100, 200), 36, False)
            self.display.show_text("Sweet dreams! 🌙", (500, 450), (100, 150, 180), 20, True)
            time.sleep(2)
            
            return True
            
        except KeyboardInterrupt:
            print("\n👋 Screensaver interrupted by user")
            return True
        except Exception as e:
            print(f"❌ Screensaver error: {e}")
            return False
        finally:
            self.display.release()


def main():
    """Main entry point."""
    print("🌙✨ Jetson Orin Nano Screensaver")
    print("Peaceful wave animation for your display")
    print("=" * 45)
    
    screensaver = JetsonScreensaver()
    
    try:
        success = screensaver.run()
        if success:
            print("🌟 Screensaver session complete")
        else:
            print("❌ Screensaver failed to start")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
