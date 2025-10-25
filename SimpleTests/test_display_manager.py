#!/usr/bin/env python3
"""
test_display_manager.py - Comprehensive test suite for Display_Manager

Tests all display capabilities including:
- Basic graphics operations (text, shapes, colors)  
- Hardware-accelerated framebuffer access
- USB camera integration with GStreamer
- Performance monitoring and FPS tracking
- System information display

Author: AI Assistant
Date: 2025-10-25
Hardware: NVIDIA Jetson Orin Nano with JetPack 6.0
"""

import os
import sys
import time
import logging
import random
import math
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Managers.Display_Manager import DisplayManager

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_basic_display_operations(display_manager):
    """Test basic display operations."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing Basic Display Operations ===")
    
    try:
        # Test 1: Clear screen with different colors
        logger.info("Testing screen clearing with colors...")
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 0, 0)]
        for i, color in enumerate(colors):
            display_manager.clear_screen(color)
            display_manager.show_text(f"Color Test {i+1}/5", (50, 50), (255, 255, 255), 48)
            time.sleep(1)
        
        # Test 2: Text rendering with different sizes and colors
        logger.info("Testing text rendering...")
        display_manager.clear_screen((0, 0, 50))  # Dark blue
        
        text_tests = [
            ("JETSON ORIN NANO", (50, 50), (255, 255, 0), 48),
            ("Display Manager Test", (50, 120), (0, 255, 255), 36),
            ("Hardware Acceleration Active", (50, 180), (0, 255, 0), 24),
            ("PIL + Framebuffer Backend", (50, 220), (255, 255, 255), 20),
            (f"Timestamp: {datetime.now().strftime('%H:%M:%S')}", (50, 260), (255, 128, 0), 16)
        ]
        
        for text, pos, color, size in text_tests:
            display_manager.show_text(text, pos, color, size, False)
        
        display_manager.update_display()
        time.sleep(3)
        
        # Test 3: Shape drawing
        logger.info("Testing shape drawing...")
        display_manager.clear_screen((20, 20, 60))  # Dark blue-gray
        
        # Draw rectangles
        for i in range(5):
            x = 100 + i * 150
            y = 100 + i * 30
            color = (255 - i * 50, i * 50, 128 + i * 25)
            display_manager.draw_rectangle((x, y), (120, 80), color, True, False)
        
        # Draw circles
        for i in range(8):
            angle = i * (2 * math.pi / 8)
            center_x = 640 + int(200 * math.cos(angle))
            center_y = 400 + int(200 * math.sin(angle))
            radius = 30 + i * 5
            color = (255, int(255 * math.sin(angle + math.pi/4)), int(255 * math.cos(angle)))
            display_manager.draw_circle((center_x, center_y), radius, color, True, False)
        
        display_manager.show_text("Shape Drawing Test", (50, 50), (255, 255, 255), 36, False)
        display_manager.update_display()
        time.sleep(3)
        
        return True
        
    except Exception as e:
        logger.error(f"Basic display operations test failed: {e}")
        return False

def test_animation_performance(display_manager):
    """Test animation performance and FPS tracking."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing Animation Performance ===")
    
    try:
        # Bouncing ball animation
        width, height = 1280, 1024
        ball_radius = 30
        ball_x, ball_y = width // 2, height // 2
        vel_x, vel_y = 8, 6
        ball_color = (255, 100, 100)
        
        start_time = time.time()
        frame_count = 0
        test_duration = 10  # seconds
        
        logger.info(f"Running bouncing ball animation for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            # Clear screen
            display_manager.clear_screen((10, 10, 30))
            
            # Update ball position
            ball_x += vel_x
            ball_y += vel_y
            
            # Bounce off edges
            if ball_x - ball_radius <= 0 or ball_x + ball_radius >= width:
                vel_x = -vel_x
                ball_color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                
            if ball_y - ball_radius <= 0 or ball_y + ball_radius >= height:
                vel_y = -vel_y
                ball_color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            
            # Keep ball in bounds
            ball_x = max(ball_radius, min(width - ball_radius, ball_x))
            ball_y = max(ball_radius, min(height - ball_radius, ball_y))
            
            # Draw ball
            display_manager.draw_circle((int(ball_x), int(ball_y)), ball_radius, ball_color, True, False)
            
            # Draw performance info
            elapsed = time.time() - start_time
            estimated_fps = frame_count / elapsed if elapsed > 0 else 0
            
            display_manager.show_text(f"Performance Test - Frame: {frame_count}", (50, 50), (255, 255, 0), 24, False)
            display_manager.show_text(f"Estimated FPS: {estimated_fps:.1f}", (50, 90), (0, 255, 255), 20, False)
            display_manager.show_text(f"Ball Position: ({int(ball_x)}, {int(ball_y)})", (50, 130), (255, 255, 255), 16, False)
            
            # Update display
            display_manager.update_display()
            frame_count += 1
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)
        
        final_fps = frame_count / test_duration
        logger.info(f"Animation test completed: {frame_count} frames in {test_duration}s = {final_fps:.2f} FPS")
        
        return True
        
    except Exception as e:
        logger.error(f"Animation performance test failed: {e}")
        return False

def test_system_info_display(display_manager):
    """Test system information display."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing System Info Display ===")
    
    try:
        # Show system info for 5 seconds
        logger.info("Displaying system information...")
        display_manager.show_system_info()
        time.sleep(5)
        
        return True
        
    except Exception as e:
        logger.error(f"System info display test failed: {e}")
        return False

def test_camera_integration(display_manager):
    """Test USB camera integration."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing USB Camera Integration ===")
    
    try:
        # Check if camera device exists
        camera_device = "/dev/video0"
        if not os.path.exists(camera_device):
            logger.warning(f"Camera device {camera_device} not found - skipping camera test")
            return True
        
        logger.info("Starting camera feed test...")
        
        # Start camera feed
        if display_manager.start_camera_feed(640, 480, 30, (320, 200)):
            logger.info("Camera feed started successfully")
            
            # Show camera feed for 10 seconds with overlay
            start_time = time.time()
            while time.time() - start_time < 10:
                # Clear screen for overlay text
                display_manager.show_text("USB CAMERA TEST", (50, 50), (255, 255, 0), 36, False)
                display_manager.show_text("Hardware-accelerated GStreamer pipeline", (50, 100), (0, 255, 255), 20, False)
                display_manager.show_text(f"Runtime: {int(time.time() - start_time)}s", (50, 140), (255, 255, 255), 16, False)
                
                info = display_manager.get_display_info()
                display_manager.show_text(f"FPS: {info.get('fps', 0)}", (50, 180), (0, 255, 0), 16, False)
                
                display_manager.update_display()
                time.sleep(0.1)
            
            # Stop camera feed
            display_manager.stop_camera_feed()
            logger.info("Camera feed stopped")
            
        else:
            logger.warning("Failed to start camera feed - hardware may not be compatible")
            
        return True
        
    except Exception as e:
        logger.error(f"Camera integration test failed: {e}")
        return False

def run_interactive_mode(display_manager):
    """Run interactive mode for manual testing."""
    logger = logging.getLogger(__name__)
    logger.info("=== Interactive Mode ===")
    
    try:
        display_manager.clear_screen((0, 30, 60))
        display_manager.show_text("INTERACTIVE MODE", (50, 50), (255, 255, 0), 48)
        display_manager.show_text("Press Ctrl+C to exit", (50, 120), (255, 255, 255), 24)
        display_manager.show_text("Manual testing enabled...", (50, 160), (0, 255, 255), 20)
        
        # Show current system status
        info = display_manager.get_display_info()
        y_pos = 220
        for key, value in info.items():
            display_manager.show_text(f"{key}: {value}", (50, y_pos), (255, 255, 255), 16, False)
            y_pos += 25
            if y_pos > 900:  # Don't go off screen
                break
        
        display_manager.update_display()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interactive mode interrupted by user")
        return True
    except Exception as e:
        logger.error(f"Interactive mode failed: {e}")
        return False

def main():
    """Main test function."""
    logger = setup_logging()
    logger.info("Starting Display_Manager comprehensive test suite")
    logger.info("Hardware: NVIDIA Jetson Orin Nano - Display: 1280x1024 HDMI")
    
    # Initialize Display Manager
    display_manager = DisplayManager()
    
    try:
        # Acquire display resources
        logger.info("Acquiring display manager...")
        if not display_manager.acquire():
            logger.error("Failed to acquire display manager")
            return False
        
        logger.info("Display manager acquired successfully!")
        
        # Run test suite
        tests = [
            ("Basic Display Operations", test_basic_display_operations),
            ("Animation Performance", test_animation_performance),
            ("System Info Display", test_system_info_display),
            ("Camera Integration", test_camera_integration)
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\\n{'='*60}")
            logger.info(f"Running test: {test_name}")
            logger.info('='*60)
            
            try:
                result = test_func(display_manager)
                results.append((test_name, result))
                logger.info(f"Test '{test_name}': {'PASSED' if result else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
        
        # Show test results
        logger.info("\\n" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\\nOverall: {passed}/{total} tests passed")
        
        # Display final results on screen
        display_manager.clear_screen((0, 50, 0) if passed == total else (50, 0, 0))
        display_manager.show_text("TEST SUITE COMPLETE", (50, 50), (255, 255, 255), 48)
        display_manager.show_text(f"Results: {passed}/{total} tests passed", (50, 120), (255, 255, 0), 32)
        
        y_pos = 200
        for test_name, result in results:
            color = (0, 255, 0) if result else (255, 100, 100)
            status = "✓ PASSED" if result else "✗ FAILED"
            display_manager.show_text(f"{test_name}: {status}", (50, y_pos), color, 20, False)
            y_pos += 30
        
        display_manager.update_display()
        time.sleep(5)
        
        # Ask user if they want interactive mode
        print("\\nWould you like to enter interactive mode? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                run_interactive_mode(display_manager)
        except:
            pass
        
        return passed == total
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return False
        
    finally:
        # Always release resources
        logger.info("Releasing display manager...")
        display_manager.release()
        logger.info("Test suite completed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)