#!/usr/bin/env python3
"""
screensaver_launcher.py

Launcher for Jetson screensavers with options.
Choose between simple breathing animation or flowing wave patterns.

Usage:
    python3 SimpleTests/screensaver_launcher.py
"""

import subprocess
import sys

sys.path.append('/home/phiip/workspace/jetson-hardware')


def show_menu():
    """Display screensaver selection menu."""
    print("🌙✨ JETSON SCREENSAVER LAUNCHER")
    print("=" * 40)
    print()
    print("Choose your screensaver:")
    print()
    print("1. 💤 Simple Breathing Colors")
    print("   - Ultra-minimal CPU usage")
    print("   - Gentle color breathing")
    print("   - 5 FPS, very low power")
    print()
    print("2. 🌊 Flowing Wave Animation") 
    print("   - Beautiful wave patterns")
    print("   - Color transitions")
    print("   - 20 FPS, smooth motion")
    print()
    print("3. ❌ Exit")
    print()


def launch_screensaver(choice: str) -> bool:
    """
    Launch the selected screensaver.
    
    Args:
        choice: User's menu choice
        
    Returns:
        bool: True if screensaver launched successfully
    """
    python_cmd = '/home/phiip/workspace/jetson-hardware/.venv/bin/python'
    
    if choice == '1':
        print("\n🌙 Launching Simple Breathing Screensaver...")
        print("💡 Perfect for overnight ambient lighting")
        print("⌨️  Press Ctrl+C to stop")
        print("-" * 40)
        
        try:
            subprocess.run([python_cmd, '/home/phiip/workspace/jetson-hardware/SimpleTests/simple_screensaver.py'])
            return True
        except KeyboardInterrupt:
            print("\n✅ Simple screensaver stopped")
            return True
        except Exception as e:
            print(f"❌ Error launching simple screensaver: {e}")
            return False
    
    elif choice == '2':
        print("\n🌊 Launching Wave Animation Screensaver...")
        print("💡 Beautiful flowing patterns with color transitions")
        print("⌨️  Press Ctrl+C to stop")
        print("-" * 40)
        
        try:
            subprocess.run([python_cmd, '/home/phiip/workspace/jetson-hardware/SimpleTests/jetson_screensaver.py'])
            return True
        except KeyboardInterrupt:
            print("\n✅ Wave screensaver stopped")
            return True
        except Exception as e:
            print(f"❌ Error launching wave screensaver: {e}")
            return False
    
    elif choice == '3':
        return False
    
    else:
        print("❌ Invalid choice, please select 1, 2, or 3")
        return None


def main():
    """Main launcher loop."""
    print("🚀 Jetson Orin Nano Screensaver System")
    print("Peaceful display animations for your Jetson")
    print()
    
    while True:
        show_menu()
        
        try:
            choice = input("Select option (1-3): ").strip()
            
            result = launch_screensaver(choice)
            
            if result is False:  # Exit chosen
                print("👋 Goodbye!")
                break
            elif result is None:  # Invalid choice
                continue
            else:  # Screensaver completed
                print("\n🌟 Screensaver session completed")
                
                # Ask if user wants to run another
                again = input("\nRun another screensaver? (y/n): ").lower().strip()
                if again not in ['y', 'yes']:
                    print("👋 Sweet dreams!")
                    break
                print()
        
        except KeyboardInterrupt:
            print("\n👋 Launcher interrupted, goodbye!")
            break
        except Exception as e:
            print(f"❌ Launcher error: {e}")
            break


if __name__ == "__main__":
    main()
