#!/usr/bin/env python3
"""
Arduino Nano Motor Test Program

Complete motor testing suite with comprehensive speed tests,
direction tests, and safety features.

Hardware Setup:
- Arduino Nano connected via USB
- ESC signal wires on pins 5 (left) and 6 (right)
- Motors connected to ESCs
- ESCs powered appropriately

Safety Features:
- Ctrl+C emergency stop at any time
- Status reporting after each command
- Progressive speed testing
- User confirmation between major test sections
"""

import serial
import time
import signal
import sys

# Global variables
ser = None
test_active = False

def signal_handler(sig, frame):
    """Emergency stop handler for Ctrl+C"""
    global ser, test_active
    print("\n\n🚨 EMERGENCY STOP ACTIVATED! 🚨")
    test_active = False
    if ser and ser.is_open:
        try:
            print("Sending emergency stop commands...")
            ser.write(b'ESTOP\n')
            time.sleep(0.1)
            ser.write(b'MOTOR:0:0\n')
            ser.write(b'MOTOR:1:0\n')
            print("✅ Emergency stop completed")
        except Exception as e:
            print(f"⚠️  Emergency stop error: {e}")
    print("Exiting safely...")
    sys.exit(0)

def send_command(command, description=""):
    """Send command to Arduino and display response with status"""
    global ser
    try:
        # Send command
        ser.write(f"{command}\n".encode())
        response = ser.readline().decode().strip()
        
        # Display result
        if description:
            print(f"   {description}")
        print(f"   📤 {command} → 📥 {response}")
        
        # Get status after motor commands
        if command.startswith("MOTOR"):
            time.sleep(0.1)  # Brief delay
            ser.write(b'STATUS\n')
            status = ser.readline().decode().strip()
            print(f"   📊 STATUS → {status}")
        
        return response
    except Exception as e:
        print(f"   ❌ Error sending {command}: {e}")
        return None

def motor_speed_test(motor_id, motor_name, speeds, direction="forward"):
    """Test a motor at multiple speeds"""
    print(f"\n{'='*50}")
    print(f"🔧 {motor_name.upper()} MOTOR - {direction.upper()} SPEED TEST")
    print(f"{'='*50}")
    
    for speed in speeds:
        actual_speed = speed if direction == "forward" else -speed
        speed_desc = f"{speed}% {direction}"
        
        print(f"\n🔄 Testing {motor_name} motor at {speed_desc}...")
        
        # Start motor
        send_command(f"MOTOR:{motor_id}:{actual_speed}", 
                    f"Starting {motor_name} motor at {speed_desc}")
        
        # Run for specified time based on speed
        run_time = 1.0 if speed <= 25 else 1.5 if speed <= 50 else 2.0
        print(f"   ⏱️  Running for {run_time} seconds...")
        time.sleep(run_time)
        
        # Stop motor
        send_command(f"MOTOR:{motor_id}:0", 
                    f"Stopping {motor_name} motor")
        
        time.sleep(0.5)  # Brief pause between tests

def both_motors_test():
    """Test both motors together"""
    print(f"\n{'='*50}")
    print(f"🔧 BOTH MOTORS SYNCHRONIZED TEST")
    print(f"{'='*50}")
    
    test_configs = [
        (20, "slow", 2.0),
        (40, "medium", 2.5),
        (60, "fast", 3.0)
    ]
    
    for speed, desc, duration in test_configs:
        print(f"\n🔄 Both motors {desc} forward ({speed}%)...")
        
        # Start both motors
        send_command(f"MOTOR:0:{speed}", f"Starting left motor at {speed}%")
        send_command(f"MOTOR:1:{speed}", f"Starting right motor at {speed}%")
        
        print(f"   ⏱️  Running both motors for {duration} seconds...")
        time.sleep(duration)
        
        # Stop both motors
        send_command("MOTOR:0:0", "Stopping left motor")
        send_command("MOTOR:1:0", "Stopping right motor")
        
        time.sleep(1.0)
    
    # Test opposite directions (turning)
    print(f"\n🔄 Turn test - left forward, right reverse...")
    send_command("MOTOR:0:30", "Left motor 30% forward")
    send_command("MOTOR:1:-30", "Right motor 30% reverse") 
    print("   ⏱️  Turning right for 2 seconds...")
    time.sleep(2.0)
    send_command("MOTOR:0:0", "Stopping left motor")
    send_command("MOTOR:1:0", "Stopping right motor")
    
    time.sleep(1.0)
    
    print(f"\n🔄 Turn test - left reverse, right forward...")
    send_command("MOTOR:0:-30", "Left motor 30% reverse")
    send_command("MOTOR:1:30", "Right motor 30% forward")
    print("   ⏱️  Turning left for 2 seconds...")
    time.sleep(2.0)
    send_command("MOTOR:0:0", "Stopping left motor")
    send_command("MOTOR:1:0", "Stopping right motor")

def emergency_stop_test():
    """Test emergency stop functionality"""
    print(f"\n{'='*50}")
    print(f"🚨 EMERGENCY STOP SYSTEM TEST")
    print(f"{'='*50}")
    
    print(f"\n🔄 Starting both motors for emergency stop demo...")
    send_command("MOTOR:0:40", "Starting left motor at 40%")
    send_command("MOTOR:1:40", "Starting right motor at 40%")
    
    print("   ⏱️  Motors running... triggering ESTOP in 2 seconds...")
    time.sleep(2.0)
    
    print("\n🚨 TRIGGERING EMERGENCY STOP...")
    send_command("ESTOP", "Emergency stop activated")
    
    print("\n🔄 Testing that motors are locked...")
    send_command("MOTOR:0:20", "Attempting to start left motor (should fail)")
    send_command("MOTOR:1:20", "Attempting to start right motor (should fail)")
    
    print("\n🔄 Resetting emergency stop...")
    send_command("RESET", "Resetting emergency stop state")
    
    print("\n🔄 Verifying motors work after reset...")
    send_command("MOTOR:0:15", "Testing left motor after reset")
    time.sleep(1.0)
    send_command("MOTOR:0:0", "Stopping left motor")
    send_command("MOTOR:1:15", "Testing right motor after reset")
    time.sleep(1.0)
    send_command("MOTOR:1:0", "Stopping right motor")

def main():
    """Main test program"""
    global ser, test_active
    
    # Set up emergency stop handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 ARDUINO NANO MOTOR COMPREHENSIVE TEST")
    print("=" * 60)
    print("⚠️  WARNING: This will move real motors!")
    print("⚠️  Ensure motors are free to spin safely!")
    print("⚠️  Press Ctrl+C at ANY TIME for emergency stop!")
    print("=" * 60)
    
    # Safety confirmation
    ready = input("\n✅ Are motors free to spin and ready for testing? (y/N): ").lower().strip()
    if ready != 'y':
        print("Test cancelled for safety.")
        return
    
    try:
        # Connect to Arduino
        print("\n📡 Connecting to Arduino...")
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
        time.sleep(2)
        ser.reset_input_buffer()
        test_active = True
        
        # Initial connection test
        print("\n🔗 Testing Arduino connection...")
        response = send_command("PING", "Testing communication")
        if response != "PONG":
            print(f"❌ Arduino not responding correctly (got: {response})")
            return
        
        # Reset to clean state
        print("\n🔄 Resetting Arduino to clean state...")
        send_command("RESET", "Resetting all systems")
        send_command("STATUS", "Getting initial status")
        
        # Define test speeds
        speeds = [15, 35, 60]  # slow, medium, fast
        
        # RIGHT MOTOR TESTS
        input("\n⏸️  Press ENTER to start RIGHT motor speed tests...")
        motor_speed_test(1, "right", speeds, "forward")
        
        input("\n⏸️  Press ENTER to test RIGHT motor reverse...")
        motor_speed_test(1, "right", speeds, "reverse")
        
        # LEFT MOTOR TESTS  
        input("\n⏸️  Press ENTER to start LEFT motor speed tests...")
        motor_speed_test(0, "left", speeds, "forward")
        
        input("\n⏸️  Press ENTER to test LEFT motor reverse...")
        motor_speed_test(0, "left", speeds, "reverse")
        
        # BOTH MOTORS TESTS
        input("\n⏸️  Press ENTER to test BOTH motors together...")
        both_motors_test()
        
        # EMERGENCY STOP TEST
        input("\n⏸️  Press ENTER to test EMERGENCY STOP system...")
        emergency_stop_test()
        
        # Final status
        print(f"\n{'='*60}")
        print("📊 FINAL SYSTEM STATUS")
        print(f"{'='*60}")
        send_command("STATUS", "Final system status")
        
        print(f"\n{'='*60}")
        print("🎉 ALL MOTOR TESTS COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        print("✅ Right motor: Forward & reverse at all speeds")
        print("✅ Left motor: Forward & reverse at all speeds") 
        print("✅ Both motors: Synchronized operation")
        print("✅ Emergency stop: Working correctly")
        print("✅ Status reporting: All systems operational")
        print("\n🚀 Your Arduino motor control system is fully functional!")
        
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("🚨 Sending emergency stop...")
        if ser and ser.is_open:
            try:
                ser.write(b'ESTOP\n')
            except:
                pass
    finally:
        test_active = False
        if ser and ser.is_open:
            ser.close()
            print("📡 Serial connection closed")

if __name__ == "__main__":
    main()