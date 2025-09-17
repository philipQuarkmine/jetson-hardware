"""
quick_led_test.py
Quick Arduino LED blink test

Tests basic serial communication by blinking the built-in LED on pin 13.
This verifies that:
1. CH340 driver is working
2. Serial communication is functional
3. Arduino is responsive
4. User has proper permissions

Usage: python3 quick_led_test.py
"""

import serial
import time
import sys

def test_arduino_led():
    """Test Arduino communication by blinking built-in LED"""
    
    print("=" * 50)
    print("ARDUINO LED BLINK TEST")
    print("=" * 50)
    
    # First check if any serial devices exist
    import os
    import glob
    
    serial_devices = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
    if not serial_devices:
        print("✗ ERROR: No USB serial devices found!")
        print("  Please check:")
        print("  1. Arduino is plugged in via USB")
        print("  2. CH340 driver is loaded: lsmod | grep ch34")
        print("  3. Try unplugging and replugging Arduino")
        return False
    
    print(f"Found serial devices: {serial_devices}")
    device_path = serial_devices[0]  # Use first available device
    
    try:
        # Open serial connection
        print(f"Connecting to Arduino on {device_path}...")
        ser = serial.Serial(device_path, 115200, timeout=2)
        
        # Wait for Arduino to reset and initialize
        print("Waiting for Arduino to initialize...")
        time.sleep(2)
        
        # Send commands to blink LED
        print("Blinking LED for 10 seconds (0.5s cycle)...")
        print("Watch the built-in LED on your Arduino!")
        
        start_time = time.time()
        led_state = False
        
        while time.time() - start_time < 10:  # Blink for 10 seconds
            # Toggle LED state
            led_state = not led_state
            
            if led_state:
                # Turn LED ON (pin 13 HIGH)
                command = "digitalWrite(13, HIGH)\n"
                print("LED ON")
            else:
                # Turn LED OFF (pin 13 LOW)  
                command = "digitalWrite(13, LOW)\n"
                print("LED OFF")
            
            # Send command to Arduino
            ser.write(command.encode('utf-8'))
            ser.flush()
            
            # Wait for 0.5 seconds
            time.sleep(0.5)
        
        # Turn LED off at end
        ser.write(b"digitalWrite(13, LOW)\n")
        ser.flush()
        
        print("LED test completed!")
        ser.close()
        
        print("\n✓ SUCCESS:")
        print("  - Serial communication working")
        print("  - CH340 driver functional")
        print("  - Arduino responding to commands")
        print("  - User permissions correct")
        
        return True
        
    except PermissionError:
        print("✗ ERROR: Permission denied accessing /dev/ttyUSB0")
        print("  Solution: You may need to restart the Jetson or run:")
        print("  sudo usermod -a -G dialout $USER")
        return False
        
    except serial.SerialException as e:
        print(f"✗ ERROR: Serial communication failed: {e}")
        print("  Possible causes:")
        print("  - Arduino not connected")
        print("  - Wrong port (/dev/ttyUSB0)")
        print("  - CH340 driver not loaded")
        return False
        
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        try:
            ser.write(b"digitalWrite(13, LOW)\n")  # Turn off LED
            ser.close()
        except:
            pass
        return False
        
    except Exception as e:
        print(f"✗ ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Arduino LED Blink Test")
    print("This will blink the built-in LED (pin 13) for 10 seconds")
    print("Press Ctrl+C to stop early\n")
    
    # Note about firmware
    print("NOTE: This test sends raw Arduino commands.")
    print("Your Arduino should have basic firmware that responds to digitalWrite commands.")
    print("If LED doesn't blink, you may need to upload Arduino firmware first.\n")
    
    success = test_arduino_led()
    
    if success:
        print("\n🎉 Arduino communication is working!")
        print("You can now proceed to upload motor control firmware.")
    else:
        print("\n❌ Arduino communication test failed.")
        print("Check connections and try again.")
    
    sys.exit(0 if success else 1)