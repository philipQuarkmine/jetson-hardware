#!/usr/bin/env python3
"""
debug_display_alignment.py - Diagnostic tool for display alignment issues

Creates simple test patterns to identify color format, alignment, and stride issues.
This will help diagnose the "sliced text" problem you're seeing.

Author: AI Assistant
Date: 2025-10-25
"""

import os
import sys
import time
import logging

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Managers.Display_Manager import DisplayManager

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    return logging.getLogger(__name__)

def test_color_channels(display_manager):
    """Test individual color channels to identify BGR/RGB issues."""
    logger = logging.getLogger(__name__)
    logger.info("Testing color channels...")
    
    # Test pure colors in sequence
    colors = [
        ("RED CHANNEL", (255, 0, 0)),
        ("GREEN CHANNEL", (0, 255, 0)), 
        ("BLUE CHANNEL", (0, 0, 255)),
        ("WHITE", (255, 255, 255)),
        ("BLACK", (0, 0, 0))
    ]
    
    for name, color in colors:
        logger.info(f"Displaying {name}: {color}")
        display_manager.clear_screen(color)
        display_manager.show_text(name, (100, 100), (255, 255, 255) if color != (255, 255, 255) else (0, 0, 0), 48, False)
        display_manager.show_text(f"RGB: {color}", (100, 200), (255, 255, 255) if color != (255, 255, 255) else (0, 0, 0), 24, False)
        display_manager.update_display()
        time.sleep(2)

def test_alignment_patterns(display_manager):
    """Test alignment with simple patterns."""
    logger = logging.getLogger(__name__)
    logger.info("Testing alignment patterns...")
    
    # Pattern 1: Vertical stripes
    display_manager.clear_screen((0, 0, 0))
    logger.info("Pattern 1: Vertical stripes (should be perfectly vertical)")
    
    for i in range(0, 1280, 40):
        color = (255, 255, 255) if (i // 40) % 2 == 0 else (0, 0, 0)
        display_manager.draw_rectangle((i, 0), (40, 1024), color, True, False)
    
    display_manager.show_text("VERTICAL STRIPES", (50, 50), (255, 0, 0), 36, False)
    display_manager.show_text("Should be perfectly aligned", (50, 100), (255, 255, 0), 24, False)
    display_manager.update_display()
    time.sleep(3)
    
    # Pattern 2: Horizontal stripes
    display_manager.clear_screen((0, 0, 0))
    logger.info("Pattern 2: Horizontal stripes (should be perfectly horizontal)")
    
    for i in range(0, 1024, 40):
        color = (255, 255, 255) if (i // 40) % 2 == 0 else (0, 0, 0)
        display_manager.draw_rectangle((0, i), (1280, 40), color, True, False)
    
    display_manager.show_text("HORIZONTAL STRIPES", (50, 50), (0, 255, 0), 36, False)
    display_manager.show_text("Should be perfectly aligned", (50, 100), (255, 255, 0), 24, False)
    display_manager.update_display()
    time.sleep(3)

def test_text_alignment(display_manager):
    """Test text rendering alignment."""
    logger = logging.getLogger(__name__)
    logger.info("Testing text alignment...")
    
    display_manager.clear_screen((50, 50, 100))
    
    # Simple text at different positions
    test_texts = [
        ("LINE 1: ABCDEFGHIJKLMNOPQRSTUVWXYZ", 50, (255, 255, 255)),
        ("LINE 2: 0123456789 !@#$%^&*()", 100, (255, 255, 0)),
        ("LINE 3: The quick brown fox jumps", 150, (0, 255, 255)),
        ("LINE 4: SIMPLE TEXT TEST", 200, (255, 0, 255)),
        ("LINE 5: Should be readable", 250, (0, 255, 0))
    ]
    
    for text, y_pos, color in test_texts:
        display_manager.show_text(text, (50, y_pos), color, 24, False)
    
    # Add grid reference points
    for x in range(100, 1200, 100):
        display_manager.draw_rectangle((x, 300), (2, 400), (100, 100, 100), True, False)
    
    for y in range(350, 700, 50):
        display_manager.draw_rectangle((50, y), (1180, 2), (100, 100, 100), True, False)
    
    display_manager.show_text("TEXT ALIGNMENT TEST", (50, 320), (255, 255, 255), 32, False)
    display_manager.show_text("Grid shows alignment", (50, 360), (200, 200, 200), 20, False)
    display_manager.update_display()
    time.sleep(5)

def test_simple_shapes(display_manager):
    """Test simple shapes for alignment."""
    logger = logging.getLogger(__name__)
    logger.info("Testing simple shapes...")
    
    display_manager.clear_screen((20, 20, 40))
    
    # Perfect squares - should appear as squares, not rectangles
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    for i, color in enumerate(colors):
        x = 100 + i * 200
        y = 200
        display_manager.draw_rectangle((x, y), (100, 100), color, True, False)
        display_manager.show_text(f"SQ{i+1}", (x + 30, y + 120), (255, 255, 255), 16, False)
    
    # Perfect circles - should appear as circles, not ovals
    for i, color in enumerate(colors):
        x = 150 + i * 200
        y = 500
        display_manager.draw_circle((x, y), 50, color, True, False)
        display_manager.show_text(f"C{i+1}", (x - 10, y + 70), (255, 255, 255), 16, False)
    
    display_manager.show_text("SHAPE TEST", (50, 50), (255, 255, 255), 36, False)
    display_manager.show_text("Squares should be square, circles should be round", (50, 100), (255, 255, 0), 20, False)
    display_manager.update_display()
    time.sleep(4)

def main():
    """Main diagnostic function."""
    logger = setup_logging()
    logger.info("=== DISPLAY ALIGNMENT DIAGNOSTIC ===")
    logger.info("This will help identify the 'sliced text' issue")
    
    display_manager = DisplayManager()
    
    try:
        if not display_manager.acquire():
            logger.error("Failed to acquire display manager")
            return False
        
        logger.info("Starting diagnostic sequence...")
        
        # Show what we're doing
        display_manager.clear_screen((0, 0, 0))
        display_manager.show_text("DIAGNOSTIC STARTING...", (100, 400), (255, 255, 0), 48)
        display_manager.show_text("Testing display alignment", (100, 500), (255, 255, 255), 24)
        display_manager.update_display()
        time.sleep(2)
        
        # Run diagnostic tests
        test_color_channels(display_manager)
        test_alignment_patterns(display_manager)
        test_text_alignment(display_manager)  
        test_simple_shapes(display_manager)
        
        # Final message
        display_manager.clear_screen((0, 50, 0))
        display_manager.show_text("DIAGNOSTIC COMPLETE", (200, 400), (255, 255, 255), 48)
        display_manager.show_text("Please describe what you saw", (200, 500), (255, 255, 0), 24)
        display_manager.update_display()
        
        logger.info("Diagnostic complete. Please describe what you observed:")
        logger.info("1. Were the color channels correct (red=red, green=green, blue=blue)?")  
        logger.info("2. Were the stripes perfectly aligned?")
        logger.info("3. Was the text readable or still 'sliced'?")
        logger.info("4. Were squares actually square and circles round?")
        
        return True
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        return False
        
    finally:
        display_manager.release()

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅' if success else '❌'} Diagnostic completed")
    print("\nPlease describe what you observed for each test pattern!")