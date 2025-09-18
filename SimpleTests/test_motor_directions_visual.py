#!/usr/bin/env python3
"""
Arduino Motor Manager Visual Verification Test

Slow, deliberate testing to visually confirm motor directions and movements.
Each test waits for user confirmation before proceeding.
"""

import sys
import time
sys.path.append('/home/phiip/jetson-hardware')

from Managers.ArduinoMotor_Manager import ArduinoMotorManager

def wait_for_user(message="Press ENTER to continue..."):
    """Wait for user input with custom message."""
    input(f"\n⏸️  {message}")

def run_movement_test(manager, left, right, description, duration=3.0):
    """Run a single movement test with user observation time."""
    print(f"\n🔄 {description}")
    print(f"   Command: set_motor_speeds(left={left}, right={right})")
    
    wait_for_user("Press ENTER to start this movement...")
    
    # Start movement
    success = manager.set_motor_speeds(left=left, right=right)
    state = manager.get_motor_state()
    
    if success:
        print(f"   ✅ Movement started: left={state.left_speed}%, right={state.right_speed}%")
        print(f"   👀 OBSERVE: {description}")
        print(f"   ⏱️  Running for {duration} seconds...")
        
        # Let it run while user observes
        time.sleep(duration)
        
        # Stop movement
        manager.stop()
        print(f"   🛑 Movement stopped")
    else:
        print(f"   ❌ Failed to start movement")
    
    # Get user feedback
    correct = input("\n❓ Did the robot move as expected? (y/N): ").lower().strip()
    if correct == 'y':
        print("   ✅ Movement verified correct!")
    else:
        print("   ⚠️  Movement needs adjustment - check wiring/motor connections")
    
    return correct == 'y'

def test_individual_motors(manager):
    """Test each motor individually to verify directions."""
    print("\n" + "="*60)
    print("🔍 INDIVIDUAL MOTOR DIRECTION VERIFICATION")
    print("="*60)
    print("Testing each motor separately to verify directions...")
    
    results = []
    
    # Left motor forward
    results.append(run_movement_test(
        manager, 40, 0, 
        "LEFT MOTOR FORWARD ONLY (right motor should be stopped)",
        duration=2.5
    ))
    
    # Left motor reverse
    results.append(run_movement_test(
        manager, -40, 0,
        "LEFT MOTOR REVERSE ONLY (right motor should be stopped)", 
        duration=2.5
    ))
    
    # Right motor forward
    results.append(run_movement_test(
        manager, 0, 40,
        "RIGHT MOTOR FORWARD ONLY (left motor should be stopped)",
        duration=2.5
    ))
    
    # Right motor reverse
    results.append(run_movement_test(
        manager, 0, -40,
        "RIGHT MOTOR REVERSE ONLY (left motor should be stopped)",
        duration=2.5
    ))
    
    print(f"\n📊 Individual Motor Test Results: {sum(results)}/{len(results)} correct")
    return all(results)

def test_combined_movements(manager):
    """Test combined motor movements for robot navigation."""
    print("\n" + "="*60)
    print("🤖 COMBINED MOVEMENT VERIFICATION") 
    print("="*60)
    print("Testing combined movements for robot navigation...")
    
    results = []
    
    # Forward movement
    results.append(run_movement_test(
        manager, 35, 35,
        "FORWARD MOVEMENT (both motors forward at same speed)",
        duration=3.0
    ))
    
    # Reverse movement
    results.append(run_movement_test(
        manager, -35, -35,
        "REVERSE MOVEMENT (both motors reverse at same speed)",
        duration=3.0
    ))
    
    # Right turn (left motor only)
    results.append(run_movement_test(
        manager, 30, 0,
        "RIGHT TURN (left motor forward, right stopped - robot should turn right)",
        duration=3.0
    ))
    
    # Left turn (right motor only)
    results.append(run_movement_test(
        manager, 0, 30,
        "LEFT TURN (right motor forward, left stopped - robot should turn left)",
        duration=3.0
    ))
    
    # Spin right (opposite directions)
    results.append(run_movement_test(
        manager, 25, -25,
        "SPIN RIGHT (left forward, right reverse - robot should spin in place)",
        duration=3.0
    ))
    
    # Spin left (opposite directions)
    results.append(run_movement_test(
        manager, -25, 25,
        "SPIN LEFT (left reverse, right forward - robot should spin in place)",
        duration=3.0
    ))
    
    print(f"\n📊 Combined Movement Test Results: {sum(results)}/{len(results)} correct")
    return all(results)

def test_high_level_helpers(manager):
    """Test the high-level movement helper functions."""
    print("\n" + "="*60)
    print("🎮 HIGH-LEVEL HELPER VERIFICATION")
    print("="*60)
    print("Testing high-level movement helpers...")
    
    helper_tests = [
        (manager.move_forward, 30, "MOVE FORWARD helper (should go straight forward)"),
        (manager.move_reverse, 30, "MOVE REVERSE helper (should go straight backward)"),
        (manager.turn_right, 25, "TURN RIGHT helper (left motor only, should turn right)"),
        (manager.turn_left, 25, "TURN LEFT helper (right motor only, should turn left)"),
    ]
    
    results = []
    
    for helper_func, speed, description in helper_tests:
        print(f"\n🔄 {description}")
        print(f"   Command: {helper_func.__name__}(speed={speed})")
        
        wait_for_user("Press ENTER to start this movement...")
        
        # Start movement
        success = helper_func(speed)
        state = manager.get_motor_state()
        
        if success:
            print(f"   ✅ Movement started: left={state.left_speed}%, right={state.right_speed}%")
            print(f"   👀 OBSERVE: {description}")
            print(f"   ⏱️  Running for 3 seconds...")
            
            time.sleep(3.0)
            
            manager.stop()
            print(f"   🛑 Movement stopped")
        else:
            print(f"   ❌ Failed to start movement")
        
        # Get user feedback
        correct = input("\n❓ Did the helper function work as expected? (y/N): ").lower().strip()
        results.append(correct == 'y')
        
        if correct == 'y':
            print("   ✅ Helper function verified correct!")
        else:
            print("   ⚠️  Helper function needs review")
    
    print(f"\n📊 Helper Function Test Results: {sum(results)}/{len(results)} correct")
    return all(results)

def main():
    """Main visual verification test."""
    print("🤖 ARDUINO MOTOR MANAGER VISUAL VERIFICATION")
    print("="*70)
    print("⚠️  This test moves motors SLOWLY so you can observe directions")
    print("⚠️  Place robot where you can clearly see motor/wheel movement")
    print("⚠️  Each test waits for your confirmation before proceeding")
    print("="*70)
    
    # Safety confirmation
    ready = input("\n✅ Is robot positioned for visual observation? (y/N): ").lower().strip()
    if ready != 'y':
        print("Test cancelled. Position robot for clear observation.")
        return
    
    try:
        with ArduinoMotorManager() as manager:
            print("\n📡 Arduino Motor Manager connected successfully!")
            
            # Test individual motors first
            motors_ok = test_individual_motors(manager)
            
            if not motors_ok:
                print("\n⚠️  Individual motor tests failed. Check wiring before continuing.")
                continue_anyway = input("Continue with combined tests anyway? (y/N): ").lower().strip()
                if continue_anyway != 'y':
                    return
            
            wait_for_user("Ready to test combined movements? Press ENTER...")
            
            # Test combined movements
            combined_ok = test_combined_movements(manager)
            
            wait_for_user("Ready to test high-level helper functions? Press ENTER...")
            
            # Test helper functions
            helpers_ok = test_high_level_helpers(manager)
            
            # Final results
            print("\n" + "="*70)
            print("🎉 VISUAL VERIFICATION COMPLETE!")
            print("="*70)
            print(f"✅ Individual motors: {'PASS' if motors_ok else 'FAIL'}")
            print(f"✅ Combined movements: {'PASS' if combined_ok else 'FAIL'}")
            print(f"✅ Helper functions: {'PASS' if helpers_ok else 'FAIL'}")
            
            if all([motors_ok, combined_ok, helpers_ok]):
                print("\n🚀 ALL MOTOR DIRECTIONS VERIFIED CORRECT!")
                print("🎯 Arduino Motor Manager is ready for voice control!")
            else:
                print("\n⚠️  Some tests failed - check motor wiring and connections")
                print("💡 Common issues:")
                print("   - Swapped motor connections (left/right)")
                print("   - Reversed motor polarity (forward/reverse)")
                print("   - ESC signal wire connections")
                
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()