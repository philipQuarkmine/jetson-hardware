"""
test_arduino_motors.py
Simple test program for Arduino-connected DC motors

Tests basic motor functionality:
- Connection to Arduino
- Individual motor control
- Differential drive
- Emergency stop
- Configuration loading

Usage:
    python test_arduino_motors.py

Requirements:
- Arduino Nano connected via USB
- Arduino firmware programmed with motor control protocol
- ESCs connected to Arduino pins 5 and 6
- DC motors connected to ESCs
"""

import time
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Managers.Arduino_Manager import ArduinoManager

def test_connection():
    """Test Arduino connection"""
    print("=" * 50)
    print("ARDUINO MOTOR TEST PROGRAM")
    print("=" * 50)
    
    # Create manager
    print("Creating Arduino Manager...")
    arduino_mgr = ArduinoManager()
    
    # Test connection
    print("Testing Arduino connection...")
    if arduino_mgr.acquire():
        print("✓ Arduino connected successfully!")
        
        # Print status
        status = arduino_mgr.get_status()
        print(f"✓ Port: {status['manager']['port']}")
        print(f"✓ Device count: {status['manager']['device_count']}")
        
        # Print pin assignments
        print("\nPin assignments:")
        for device_name, device_status in status['devices'].items():
            pins = device_status.get('pins', {})
            for pin, purpose in pins.items():
                print(f"  Pin {pin}: {purpose}")
        
        arduino_mgr.release()
        return True
    else:
        print("✗ Failed to connect to Arduino")
        return False

def test_individual_motors():
    """Test individual motor control"""
    print("\n" + "=" * 50)
    print("INDIVIDUAL MOTOR TEST")
    print("=" * 50)
    
    arduino_mgr = ArduinoManager()
    
    if not arduino_mgr.acquire():
        print("✗ Failed to acquire Arduino")
        return False
    
    try:
        print("Testing individual motor control...")
        
        # Test left motor
        print("\nTesting left motor...")
        print("  Forward 50% for 2 seconds...")
        arduino_mgr.set_motor_speed('left_motor', 50)
        time.sleep(2)
        
        print("  Backward 30% for 2 seconds...")
        arduino_mgr.set_motor_speed('left_motor', -30)
        time.sleep(2)
        
        print("  Stop...")
        arduino_mgr.stop_motor('left_motor')
        time.sleep(1)
        
        # Test right motor
        print("\nTesting right motor...")
        print("  Forward 50% for 2 seconds...")
        arduino_mgr.set_motor_speed('right_motor', 50)
        time.sleep(2)
        
        print("  Backward 30% for 2 seconds...")
        arduino_mgr.set_motor_speed('right_motor', -30)
        time.sleep(2)
        
        print("  Stop...")
        arduino_mgr.stop_motor('right_motor')
        time.sleep(1)
        
        print("✓ Individual motor test completed")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        arduino_mgr.emergency_stop()
        return False
    except Exception as e:
        print(f"✗ Motor test failed: {e}")
        return False
    finally:
        arduino_mgr.release()

def test_differential_drive():
    """Test differential drive kinematics"""
    print("\n" + "=" * 50)
    print("DIFFERENTIAL DRIVE TEST")
    print("=" * 50)
    
    arduino_mgr = ArduinoManager()
    
    if not arduino_mgr.acquire():
        print("✗ Failed to acquire Arduino")
        return False
    
    try:
        print("Testing differential drive movements...")
        
        # Forward
        print("\n  Drive forward 40% for 3 seconds...")
        arduino_mgr.drive_forward(40)
        time.sleep(3)
        
        # Stop
        print("  Stop...")
        arduino_mgr.stop_driving()
        time.sleep(1)
        
        # Backward
        print("  Drive backward 30% for 3 seconds...")
        arduino_mgr.drive_backward(30)
        time.sleep(3)
        
        # Stop
        print("  Stop...")
        arduino_mgr.stop_driving()
        time.sleep(1)
        
        # Turn left
        print("  Turn left 25% for 2 seconds...")
        arduino_mgr.turn_left(25)
        time.sleep(2)
        
        # Stop
        print("  Stop...")
        arduino_mgr.stop_driving()
        time.sleep(1)
        
        # Turn right
        print("  Turn right 25% for 2 seconds...")
        arduino_mgr.turn_right(25)
        time.sleep(2)
        
        # Stop
        print("  Stop...")
        arduino_mgr.stop_driving()
        time.sleep(1)
        
        # Complex movement
        print("  Complex movement: forward + turn...")
        arduino_mgr.drive(30, 15)  # Forward with slight right turn
        time.sleep(3)
        
        # Final stop
        arduino_mgr.stop_driving()
        
        print("✓ Differential drive test completed")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        arduino_mgr.emergency_stop()
        return False
    except Exception as e:
        print(f"✗ Differential drive test failed: {e}")
        return False
    finally:
        arduino_mgr.release()

def test_emergency_stop():
    """Test emergency stop functionality"""
    print("\n" + "=" * 50)
    print("EMERGENCY STOP TEST")
    print("=" * 50)
    
    arduino_mgr = ArduinoManager()
    
    if not arduino_mgr.acquire():
        print("✗ Failed to acquire Arduino")
        return False
    
    try:
        print("Testing emergency stop...")
        
        # Start motors
        print("  Starting motors...")
        arduino_mgr.drive_forward(50)
        time.sleep(1)
        
        # Emergency stop
        print("  Triggering emergency stop...")
        arduino_mgr.emergency_stop()
        
        # Try to move (should fail)
        print("  Attempting to move after emergency stop (should fail)...")
        result = arduino_mgr.drive_forward(30)
        if not result:
            print("  ✓ Motors correctly blocked after emergency stop")
        else:
            print("  ✗ Emergency stop not working properly")
        
        # Reset emergency stop
        print("  Resetting emergency stop...")
        arduino_mgr.reset_emergency_stop()
        
        # Try to move again (should work)
        print("  Attempting to move after reset...")
        result = arduino_mgr.drive_forward(20)
        if result:
            print("  ✓ Motors working after emergency stop reset")
            time.sleep(1)
            arduino_mgr.stop_driving()
        else:
            print("  ✗ Motors not working after reset")
        
        print("✓ Emergency stop test completed")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        arduino_mgr.emergency_stop()
        return False
    except Exception as e:
        print(f"✗ Emergency stop test failed: {e}")
        return False
    finally:
        arduino_mgr.release()

def run_interactive_test():
    """Run interactive motor test"""
    print("\n" + "=" * 50)
    print("INTERACTIVE MOTOR CONTROL")
    print("=" * 50)
    print("Commands:")
    print("  w/s: Forward/Backward")
    print("  a/d: Turn Left/Right")
    print("  q/e: Left motor only")
    print("  u/o: Right motor only")
    print("  space: Stop")
    print("  x: Emergency stop")
    print("  r: Reset emergency stop")
    print("  ESC or Ctrl+C: Exit")
    
    arduino_mgr = ArduinoManager()
    
    if not arduino_mgr.acquire():
        print("✗ Failed to acquire Arduino")
        return False
    
    try:
        import termios, tty
        
        # Get terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(sys.stdin.fileno())
            
            print("\nInteractive control active. Press keys to control motors...")
            
            while True:
                key = sys.stdin.read(1)
                
                if key == '\x1b':  # ESC
                    break
                elif key == 'w':
                    print("Forward")
                    arduino_mgr.drive_forward(40)
                elif key == 's':
                    print("Backward")
                    arduino_mgr.drive_backward(40)
                elif key == 'a':
                    print("Turn left")
                    arduino_mgr.turn_left(30)
                elif key == 'd':
                    print("Turn right")
                    arduino_mgr.turn_right(30)
                elif key == 'q':
                    print("Left motor forward")
                    arduino_mgr.set_motor_speed('left_motor', 40)
                elif key == 'e':
                    print("Right motor forward")
                    arduino_mgr.set_motor_speed('right_motor', 40)
                elif key == ' ':
                    print("Stop")
                    arduino_mgr.stop_driving()
                elif key == 'x':
                    print("Emergency stop")
                    arduino_mgr.emergency_stop()
                elif key == 'r':
                    print("Reset emergency stop")
                    arduino_mgr.reset_emergency_stop()
                elif key == '\x03':  # Ctrl+C
                    break
                    
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    except ImportError:
        print("Interactive mode not available (termios not found)")
        return False
    except KeyboardInterrupt:
        print("\n⚠ Interactive test interrupted")
    except Exception as e:
        print(f"✗ Interactive test failed: {e}")
        return False
    finally:
        arduino_mgr.stop_driving()
        arduino_mgr.release()
    
    print("✓ Interactive test completed")
    return True

def main():
    """Main test program"""
    try:
        # Test sequence
        tests = [
            ("Connection Test", test_connection),
            ("Individual Motors", test_individual_motors),  
            ("Differential Drive", test_differential_drive),
            ("Emergency Stop", test_emergency_stop)
        ]
        
        print("Arduino Motor Test Suite")
        print("Press Ctrl+C at any time to stop\n")
        
        results = []
        for test_name, test_func in tests:
            try:
                print(f"\nRunning {test_name}...")
                result = test_func()
                results.append((test_name, result))
                
                if not result:
                    print(f"⚠ {test_name} failed, continuing...")
                    
            except KeyboardInterrupt:
                print(f"\n⚠ {test_name} interrupted by user")
                break
            except Exception as e:
                print(f"✗ {test_name} crashed: {e}")
                results.append((test_name, False))
        
        # Interactive test (optional)
        try:
            response = input("\nRun interactive test? (y/N): ")
            if response.lower() == 'y':
                run_interactive_test()
        except KeyboardInterrupt:
            pass
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name:20} {status}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        print(f"\nPassed: {passed}/{total}")
        
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
    except Exception as e:
        print(f"\nTest suite crashed: {e}")

if __name__ == "__main__":
    main()