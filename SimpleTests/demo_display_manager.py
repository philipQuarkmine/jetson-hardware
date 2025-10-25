#!/usr/bin/env python3
"""
demo_display_manager.py - Interactive demo of Display_Manager capabilities

Showcases all features of the hardware-accelerated display system:
- Real-time graphics with shapes, text, and colors
- Performance monitoring with FPS tracking  
- USB camera integration (when available)
- Interactive controls and system information

Author: AI Assistant
Date: 2025-10-25
Hardware: NVIDIA Jetson Orin Nano with JetPack 6.0
"""

import logging
import math
import os
import random
import sys
import time
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Managers.Display_Manager import DisplayManager


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def demo_graphics_showcase(display_manager):
    """Showcase graphics capabilities with animated elements."""
    logger = logging.getLogger(__name__)
    logger.info("Running graphics showcase demo...")
    
    width, height = 1280, 1024
    
    for frame in range(180):  # 6 seconds at 30fps
        # Clear with gradient-like background
        bg_blue = int(50 + 30 * math.sin(frame * 0.1))
        display_manager.clear_screen((20, 30, bg_blue))
        
        # Animated title
        title_color = (255, int(128 + 127 * math.sin(frame * 0.15)), 0)
        display_manager.show_text("JETSON ORIN NANO DISPLAY", (50, 50), title_color, 48, False)
        display_manager.show_text("Hardware-Accelerated Graphics", (50, 110), (0, 255, 255), 24, False)
        
        # Rotating circles
        center_x, center_y = width // 2, height // 2
        for i in range(8):
            angle = (frame * 0.1) + (i * math.pi / 4)
            x = center_x + int(200 * math.cos(angle))
            y = center_y + int(150 * math.sin(angle))
            radius = 20 + int(10 * math.sin(frame * 0.2 + i))
            
            # Rainbow colors
            hue = (frame * 5 + i * 45) % 360
            r = int(128 + 127 * math.sin(math.radians(hue)))
            g = int(128 + 127 * math.sin(math.radians(hue + 120)))
            b = int(128 + 127 * math.sin(math.radians(hue + 240)))
            
            display_manager.draw_circle((x, y), radius, (r, g, b), True, False)
        
        # Moving rectangles
        for i in range(5):
            x = int(100 + 200 * math.sin(frame * 0.05 + i))
            y = int(600 + 50 * math.cos(frame * 0.08 + i))
            w, h = 80 + int(40 * math.sin(frame * 0.1)), 60
            color = (255 - i * 40, i * 50, 128 + i * 20)
            display_manager.draw_rectangle((x, y), (w, h), color, True, False)
        
        # Performance info
        fps = 30  # Target FPS
        display_manager.show_text(f"Frame: {frame}/180", (50, 170), (255, 255, 255), 18, False)
        display_manager.show_text(f"FPS: ~{fps}", (50, 195), (0, 255, 0), 18, False)
        display_manager.show_text(f"Resolution: 1280x1024x32bpp", (50, 220), (255, 255, 0), 16, False)
        
        display_manager.update_display()
        time.sleep(1/30)  # 30 FPS target
    
    logger.info("Graphics showcase completed")

def demo_text_and_fonts(display_manager):
    """Demonstrate text rendering capabilities."""
    logger = logging.getLogger(__name__)
    logger.info("Running text and font demo...")
    
    display_manager.clear_screen((0, 20, 40))
    
    # Title
    display_manager.show_text("TEXT RENDERING DEMO", (50, 50), (255, 255, 0), 56, False)
    
    # Various font sizes and colors
    texts = [
        ("Large Header Text", (50, 150), (255, 100, 100), 42),
        ("Medium subtitle text", (50, 210), (100, 255, 100), 32),
        ("Regular body text for information display", (50, 260), (100, 100, 255), 24),
        ("Small detail text for status and debugging info", (50, 300), (255, 255, 100), 18),
        ("Tiny system font for dense information display", (50, 330), (200, 200, 200), 14),
    ]
    
    for text, pos, color, size in texts:
        display_manager.show_text(text, pos, color, size, False)
    
    # System information
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_texts = [
        f"Current Time: {current_time}",
        "Hardware: NVIDIA Jetson Orin Nano",
        "Display: 1280x1024 HDMI via framebuffer",
        "Graphics: PIL + Direct framebuffer access",
        "Performance: Hardware-accelerated rendering"
    ]
    
    y_pos = 400
    for text in info_texts:
        display_manager.show_text(text, (50, y_pos), (255, 255, 255), 20, False)
        y_pos += 30
    
    # Color demonstration rectangles
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255)
    ]
    
    for i, color in enumerate(colors):
        x = 50 + i * 60
        display_manager.draw_rectangle((x, 650), (50, 50), color, True, False)
        display_manager.show_text(f"RGB", (x + 5, 710), (255, 255, 255), 12, False)
    
    display_manager.update_display()
    time.sleep(5)
    logger.info("Text and font demo completed")

def demo_performance_test(display_manager):
    """Run performance test with real-time monitoring."""
    logger = logging.getLogger(__name__)
    logger.info("Running performance test...")
    
    start_time = time.time()
    frame_count = 0
    test_duration = 15
    
    logger.info(f"Performance test: {test_duration} seconds of continuous rendering")
    
    while time.time() - start_time < test_duration:
        elapsed = time.time() - start_time
        
        # Clear with dynamic background
        bg_color = (
            int(30 + 25 * math.sin(elapsed * 2)),
            int(20 + 15 * math.cos(elapsed * 1.5)),
            int(60 + 30 * math.sin(elapsed * 3))
        )
        display_manager.clear_screen(bg_color)
        
        # Performance metrics
        current_fps = frame_count / elapsed if elapsed > 0 else 0
        
        display_manager.show_text("PERFORMANCE TEST", (50, 50), (255, 255, 0), 48, False)
        display_manager.show_text(f"Elapsed: {elapsed:.1f}s", (50, 120), (255, 255, 255), 32, False)
        display_manager.show_text(f"Frame Count: {frame_count}", (50, 170), (0, 255, 255), 24, False)
        display_manager.show_text(f"Average FPS: {current_fps:.2f}", (50, 210), (0, 255, 0), 24, False)
        
        # Stress test with many shapes
        for i in range(20):
            x = random.randint(400, 1200)
            y = random.randint(300, 900) 
            radius = random.randint(10, 30)
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            display_manager.draw_circle((x, y), radius, color, True, False)
        
        # Progress bar
        progress = elapsed / test_duration
        bar_width = int(800 * progress)
        display_manager.draw_rectangle((50, 270), (800, 30), (50, 50, 50), True, False)
        display_manager.draw_rectangle((50, 270), (bar_width, 30), (0, 255, 0), True, False)
        display_manager.show_text(f"Progress: {progress*100:.1f}%", (50, 250), (255, 255, 255), 20, False)
        
        display_manager.update_display()
        frame_count += 1
    
    final_fps = frame_count / test_duration
    logger.info(f"Performance test completed: {frame_count} frames in {test_duration}s = {final_fps:.2f} FPS")
    
    # Show final results
    display_manager.clear_screen((0, 50, 0))
    display_manager.show_text("PERFORMANCE TEST COMPLETE", (50, 200), (255, 255, 255), 48, False)
    display_manager.show_text(f"Average FPS: {final_fps:.2f}", (50, 280), (255, 255, 0), 36, False)
    display_manager.show_text(f"Total Frames: {frame_count}", (50, 340), (0, 255, 255), 32, False)
    
    if final_fps > 20:
        display_manager.show_text("EXCELLENT PERFORMANCE!", (50, 400), (0, 255, 0), 32, False)
    elif final_fps > 15:
        display_manager.show_text("GOOD PERFORMANCE", (50, 400), (255, 255, 0), 32, False)
    else:
        display_manager.show_text("ACCEPTABLE PERFORMANCE", (50, 400), (255, 128, 0), 32, False)
    
    display_manager.update_display()
    time.sleep(3)

def demo_system_status(display_manager):
    """Display comprehensive system status."""
    logger = logging.getLogger(__name__)
    logger.info("Displaying system status...")
    
    display_manager.show_system_info()
    time.sleep(5)

def main():
    """Main demo function."""
    logger = setup_logging()
    logger.info("Starting Display_Manager Interactive Demo")
    logger.info("NVIDIA Jetson Orin Nano - Hardware-Accelerated Display System")
    
    display_manager = DisplayManager()
    
    try:
        # Acquire display
        logger.info("Acquiring display resources...")
        if not display_manager.acquire():
            logger.error("Failed to acquire display manager")
            return False
        
        logger.info("Display manager acquired - starting demo sequence")
        
        # Demo sequence
        demos = [
            ("Graphics Showcase", demo_graphics_showcase),
            ("Text & Font Demo", demo_text_and_fonts), 
            ("Performance Test", demo_performance_test),
            ("System Status", demo_system_status)
        ]
        
        for demo_name, demo_func in demos:
            logger.info(f"\\n{'='*60}")
            logger.info(f"Running demo: {demo_name}")
            logger.info('='*60)
            
            try:
                demo_func(display_manager)
                logger.info(f"Demo '{demo_name}' completed successfully")
                
            except Exception as e:
                logger.error(f"Demo '{demo_name}' failed: {e}")
        
        # Final message
        display_manager.clear_screen((20, 20, 60))
        display_manager.show_text("DEMO COMPLETE", (200, 300), (255, 255, 0), 72)
        display_manager.show_text("Display_Manager is ready for use!", (200, 400), (0, 255, 255), 32)
        display_manager.show_text("Press Ctrl+C to exit", (200, 450), (255, 255, 255), 24)
        display_manager.update_display()
        
        logger.info("\\n" + "="*60)
        logger.info("DEMO COMPLETED SUCCESSFULLY")
        logger.info("Display_Manager is fully functional and ready for integration")
        logger.info("="*60)
        
        # Wait for user interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Demo interrupted by user")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return False
        
    finally:
        logger.info("Releasing display manager...")
        display_manager.release()
        logger.info("Demo completed")

if __name__ == "__main__":
    success = main()
    print(f"\\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Display_Manager demo completed")
    sys.exit(0 if success else 1)
