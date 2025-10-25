#!/usr/bin/env python3
"""
simple_screensaver.py

Minimal, peaceful screensaver for Jetson display.
Simple breathing color animation - very gentle and low power.

Usage:
    python3 SimpleTests/simple_screensaver.py
"""

import math
import signal
import sys
import time

sys.path.append('/home/phiip/workspace/jetson-hardware')

from Managers.Display_Manager import DisplayManager


class SimpleScreensaver:
    """
    Ultra-simple breathing color screensaver.
    
    Features:
    - Gentle breathing animation (fade in/out)
    - Single peaceful color that slowly shifts
    - Very low brightness
    - Minimal CPU usage
    """
    
    def __init__(self):
        self.display = DisplayManager()
        self.running = False
        self.start_time = time.time()
    
    def setup_exit_handler(self):
        """Setup graceful exit."""
        def exit_handler(signum, frame):
            print("\n🌙 Stopping screensaver...")
            self.running = False
        
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)
    
    def get_breathing_color(self, t: float) -> tuple:
        """
        Get current color for breathing animation.
        
        Args:
            t: Time in seconds
            
        Returns:
            tuple: (R, G, B) color values
        """
        # Slower breathing cycle (20 seconds per full cycle) - more noticeable
        breath_cycle = math.sin(t * 0.15) * 0.5 + 0.5  # 0 to 1
        
        # Color shift cycle (2 minutes per color change)
        color_cycle = (t * 0.008) % 1.0
        
        # Base colors (peaceful but more vibrant for visibility)
        if color_cycle < 0.25:
            # Deep blue to purple
            base_r, base_g, base_b = 35, 45, 80
        elif color_cycle < 0.5:
            # Purple to green
            base_r, base_g, base_b = 55, 35, 70
        elif color_cycle < 0.75:
            # Green to amber
            base_r, base_g, base_b = 35, 60, 35
        else:
            # Amber to blue
            base_r, base_g, base_b = 70, 55, 30
        
        # Apply breathing intensity (more noticeable range)
        intensity = 0.15 + (breath_cycle * 0.7)  # 15% to 85% intensity - much more visible
        
        r = int(base_r * intensity)
        g = int(base_g * intensity)
        b = int(base_b * intensity)
        
        return (r, g, b)
    
    def run(self):
        """Run the simple screensaver."""
        print("🌙 Simple Jetson Screensaver Starting...")
        
        if not self.display.acquire():
            print("❌ Could not acquire display")
            return False
        
        try:
            self.setup_exit_handler()
            
            # Show startup
            self.display.clear_screen((30, 30, 50))
            self.display.show_text("PEACEFUL MODE", (500, 400), (80, 100, 120), 32, False)
            self.display.show_text("Press Ctrl+C to exit", (480, 450), (60, 80, 100), 16, True)
            time.sleep(3)
            
            print("💤 Entering peaceful mode... (Ctrl+C to exit)")
            
            # Main loop
            self.running = True
            frame_count = 0
            
            while self.running:
                t = time.time() - self.start_time
                
                # Get breathing color
                color = self.get_breathing_color(t)
                
                # Simply fill screen with breathing color
                self.display.clear_screen(color)
                self.display.update_display()
                
                frame_count += 1
                
                # Higher frame rate for smoother breathing transitions
                time.sleep(0.067)  # 15 FPS - much smoother brightness changes
            
            # Goodbye
            self.display.clear_screen((20, 20, 30))
            self.display.show_text("GOOD NIGHT 🌙", (500, 400), (100, 120, 140), 28, True)
            time.sleep(2)
            
            runtime = time.time() - self.start_time
            print(f"✅ Screensaver ran for {runtime:.1f} seconds ({frame_count} frames)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            self.display.release()


def main():
    """Run simple screensaver."""
    screensaver = SimpleScreensaver()
    screensaver.run()


if __name__ == "__main__":
    main()
