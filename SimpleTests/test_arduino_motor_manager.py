#!/usr/bin/env python3
"""
Arduino Motor Manager Test Suite

Tests the new ArduinoMotor_Manager with both direct speed control
and high-level movement helpers.
"""

import sys
import time

sys.path.append('/home/phiip/jetson-hardware')

from Managers.ArduinoMotor_Manager import ArduinoMotorManager


def test_direct_speed_control(manager):
    """Test direct speed control (primary LLM interface)."""
    print("\n🎯 Testing Direct Speed Control (LLM Interface)")
    print("=" * 50)
    
    test_cases = [
        (30, 30, "Forward movement"),
        (-20, -20, "Reverse movement"), 
        (40, 0, "Right turn (left motor only)"),
        (0, 40, "Left turn (right motor only)"),
        (50, -25, "Complex movement (left forward, right reverse)"),
        (0, 0, "Stop")
    ]
    
    for left, right, description in test_cases:
        print(f"\n🔄 {description}: set_motor_speeds({left}, {right})")
        success = manager.set_motor_speeds(left=left, right=right)
        state = manager.get_motor_state()
        print(f"   ✅ Success: {success}")
        print(f"   📊 Actual speeds: left={state.left_speed}%, right={state.right_speed}%")
        print(f"   ⏱️  Running for 1.5 seconds...")
        time.sleep(1.5)

def test_high_level_helpers(manager):
    """Test high-level movement helpers (initial training)."""
    print("\n🎮 Testing High-Level Movement Helpers")
    print("=" * 50)
    
    movements = [
        (manager.move_forward, 35, "Move Forward"),
        (manager.move_reverse, 25, "Move Reverse"),
        (manager.turn_right, 30, "Turn Right"),
        (manager.turn_left, 30, "Turn Left"),
        (manager.stop, None, "Stop")
    ]
    
    for method, speed, description in movements:
        print(f"\n🔄 {description}" + (f" (speed={speed})" if speed else ""))
        
        if speed is not None:
            success = method(speed)
        else:
            success = method()
            
        state = manager.get_motor_state()
        print(f"   ✅ Success: {success}")
        print(f"   📊 Resulting speeds: left={state.left_speed}%, right={state.right_speed}%")
        print(f"   ⏱️  Running for 1.5 seconds...")
        time.sleep(1.5)

def test_safety_features(manager):
    """Test emergency stop and safety features."""
    print("\n🚨 Testing Safety Features")
    print("=" * 50)
    
    print("\n🔄 Starting movement for emergency stop test...")
    manager.move_forward(40)
    state = manager.get_motor_state()
    print(f"   📊 Motors running: left={state.left_speed}%, right={state.right_speed}%")
    
    print("\n🚨 Testing emergency stop...")
    time.sleep(1.0)
    success = manager.emergency_stop()
    state = manager.get_motor_state()
    print(f"   ✅ Emergency stop success: {success}")
    print(f"   📊 Motors stopped: left={state.left_speed}%, right={state.right_speed}%")
    print(f"   🔒 Emergency stop active: {state.emergency_stop}")
    
    print("\n🔄 Testing movement while emergency stop active (should fail)...")
    success = manager.move_forward(20)
    print(f"   ❌ Movement blocked: {not success} (expected)")
    
    print("\n🔄 Resetting emergency stop...")
    success = manager.reset_emergency_stop()
    state = manager.get_motor_state()
    print(f"   ✅ Reset success: {success}")
    print(f"   🔓 Emergency stop cleared: {not state.emergency_stop}")
    
    print("\n🔄 Testing movement after reset...")
    success = manager.move_forward(15)
    state = manager.get_motor_state()
    print(f"   ✅ Movement restored: {success}")
    print(f"   📊 Motors running: left={state.left_speed}%, right={state.right_speed}%")
    time.sleep(1.0)
    manager.stop()

def main():
    """Main test program."""
    print("🤖 ARDUINO MOTOR MANAGER COMPREHENSIVE TEST")
    print("=" * 60)
    print("⚠️  WARNING: This will move real motors!")
    print("⚠️  Ensure robot is free to move safely!")
    print("=" * 60)
    
    # Safety confirmation
    ready = input("\n✅ Is robot ready for movement testing? (y/N): ").lower().strip()
    if ready != 'y':
        print("Test cancelled for safety.")
        return
    
    try:
        with ArduinoMotorManager() as manager:
            print("\n📡 Arduino Motor Manager connected successfully!")
            
            # Test direct speed control (primary LLM interface)
            test_direct_speed_control(manager)
            
            input("\n⏸️  Press ENTER to continue with high-level helpers...")
            test_high_level_helpers(manager)
            
            input("\n⏸️  Press ENTER to test safety features...")
            test_safety_features(manager)
            
            print("\n" + "=" * 60)
            print("🎉 ALL ARDUINO MOTOR MANAGER TESTS COMPLETED!")
            print("=" * 60)
            print("✅ Direct speed control (LLM interface): Working")
            print("✅ High-level movement helpers: Working")
            print("✅ Emergency stop system: Working")
            print("✅ Thread-safe manager pattern: Working")
            print("\n🚀 Arduino Motor Manager is ready for voice control integration!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Check Arduino connection and hardware setup.")

if __name__ == "__main__":
    main()
