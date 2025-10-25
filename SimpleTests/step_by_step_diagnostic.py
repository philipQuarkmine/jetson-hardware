#!/usr/bin/env python3
"""
step_by_step_diagnostic.py - One test at a time for accurate diagnosis

Runs individual diagnostic tests with pauses between each one to get 
precise feedback on the display alignment issues.

Author: AI Assistant
Date: 2025-10-25
"""

import logging
import os
import sys
import time

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Managers.Display_Manager import DisplayManager


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    return logging.getLogger(__name__)

def wait_for_user():
    """Wait for user to press Enter before continuing."""
    input("Press Enter when ready for the next test...")

def test_1_solid_red(display_manager):
    """Test 1: Pure solid red screen."""
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 1: SOLID RED SCREEN ===")
    
    display_manager.clear_screen((255, 0, 0))  # Pure red
    display_manager.update_display()
    
    print("\n🔴 TEST 1: You should see a PURE RED screen")
    print("Question: Is the entire screen red, or do you see other colors?")
    print("If you see blue instead of red, we have a BGR/RGB issue.")
    wait_for_user()

def test_2_solid_green(display_manager):
    """Test 2: Pure solid green screen."""
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 2: SOLID GREEN SCREEN ===")
    
    display_manager.clear_screen((0, 255, 0))  # Pure green
    display_manager.update_display()
    
    print("\n🟢 TEST 2: You should see a PURE GREEN screen")
    print("Question: Is the entire screen green?")
    wait_for_user()

def test_3_solid_blue(display_manager):
    """Test 3: Pure solid blue screen.""" 
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 3: SOLID BLUE SCREEN ===")
    
    display_manager.clear_screen((0, 0, 255))  # Pure blue
    display_manager.update_display()
    
    print("\n🔵 TEST 3: You should see a PURE BLUE screen")
    print("Question: Is the entire screen blue?")
    print("If you see red instead of blue, we definitely have BGR/RGB swapped.")
    wait_for_user()

def test_4_simple_text(display_manager):
    """Test 4: Simple white text on black background."""
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 4: SIMPLE TEXT ===")
    
    display_manager.clear_screen((0, 0, 0))  # Black background
    display_manager.show_text("HELLO WORLD", (100, 200), (255, 255, 255), 48)  # White text
    display_manager.update_display()
    
    print("\n📝 TEST 4: White text 'HELLO WORLD' on black background")
    print("Question: Can you read 'HELLO WORLD' clearly?")
    print("Or does the text look sliced/shifted/garbled?")
    wait_for_user()

def test_5_vertical_stripes(display_manager):
    """Test 5: Simple vertical black and white stripes."""
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 5: VERTICAL STRIPES ===")
    
    display_manager.clear_screen((0, 0, 0))  # Start with black
    
    # Create 10 wide vertical stripes
    for i in range(0, 1280, 100):
        if (i // 100) % 2 == 0:  # Every other stripe white
            display_manager.draw_rectangle((i, 0), (100, 1024), (255, 255, 255), True, False)
    
    display_manager.update_display()
    
    print("\n📏 TEST 5: Vertical black and white stripes")
    print("Question: Do you see perfectly straight vertical stripes?")
    print("Or are they jagged/shifted/misaligned?")
    wait_for_user()

def test_6_horizontal_stripes(display_manager):
    """Test 6: Simple horizontal black and white stripes."""
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 6: HORIZONTAL STRIPES ===")
    
    display_manager.clear_screen((0, 0, 0))  # Start with black
    
    # Create horizontal stripes
    for i in range(0, 1024, 80):
        if (i // 80) % 2 == 0:  # Every other stripe white
            display_manager.draw_rectangle((0, i), (1280, 80), (255, 255, 255), True, False)
    
    display_manager.update_display()
    
    print("\n📏 TEST 6: Horizontal black and white stripes")
    print("Question: Do you see perfectly straight horizontal stripes?")
    print("Or are they jagged/shifted/misaligned?")
    wait_for_user()

def test_7_large_text_readable(display_manager):
    """Test 7: Large readable text."""
    logger = logging.getLogger(__name__)
    logger.info("=== TEST 7: LARGE TEXT READABILITY ===")
    
    display_manager.clear_screen((50, 50, 100))  # Dark blue background
    display_manager.show_text("ABCDEFGHIJKLM", (50, 200), (255, 255, 0), 72)  # Large yellow text
    display_manager.show_text("NOPQRSTUVWXYZ", (50, 350), (255, 255, 0), 72)
    display_manager.show_text("1234567890", (50, 500), (255, 255, 0), 72)
    display_manager.update_display()
    
    print("\n🔤 TEST 7: Large alphabet and numbers")
    print("Question: Can you clearly read all the letters and numbers?")
    print("Are they crisp and clear, or sliced/distorted?")
    wait_for_user()

def main():
    """Main step-by-step diagnostic."""
    logger = setup_logging()
    logger.info("=== STEP-BY-STEP DISPLAY DIAGNOSTIC ===")
    
    print("\n🔧 DISPLAY DIAGNOSTIC - ONE TEST AT A TIME")
    print("We'll run 7 simple tests to identify the display issue.")
    print("Please observe each test carefully and answer the questions.")
    
    display_manager = DisplayManager()
    
    try:
        if not display_manager.acquire():
            logger.error("Failed to acquire display manager")
            return False
        
        print("\n✅ Display manager ready. Starting tests...")
        wait_for_user()
        
        # Run tests one by one
        tests = [
            test_1_solid_red,
            test_2_solid_green, 
            test_3_solid_blue,
            test_4_simple_text,
            test_5_vertical_stripes,
            test_6_horizontal_stripes,
            test_7_large_text_readable
        ]
        
        for i, test_func in enumerate(tests, 1):
            print(f"\n{'='*50}")
            print(f"RUNNING TEST {i} OF {len(tests)}")
            print('='*50)
            test_func(display_manager)
        
        # Final summary
        display_manager.clear_screen((0, 100, 0))  # Green background
        display_manager.show_text("ALL TESTS COMPLETE", (200, 400), (255, 255, 255), 48)
        display_manager.show_text("Ready for your feedback!", (200, 500), (255, 255, 0), 24)
        display_manager.update_display()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("Now please tell me what you observed in each test.")
        
        return True
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        return False
        
    finally:
        display_manager.release()

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅' if success else '❌'} Diagnostic completed")
    print("\nPlease describe what you saw in each test!")
