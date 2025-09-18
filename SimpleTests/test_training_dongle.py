#!/usr/bin/env python3
"""
Test script for 4-key USB training dongle

This script tests the training dongle functionality and helps with:
- Hardware detection and verification
- Key mapping discovery and calibration  
- Manager interface validation
- Real-ti        print("Key 1 = EXCELLENT 😍 (Best!)")
        print("Key 2 = GOOD     😊")
        print("Key 3 = POOR     😬")
        print("Key 4 = FAILURE  💥 (Worst!)")eedback monitoring demonstration

Usage:
    python test_training_dongle.py [options]
    
Options:
    --duration N    Test duration in seconds (default: 15)
    --manager       Test through manager interface (default: direct lib)
    --calibrate     Discover key mappings by testing each key
    --export        Export test results to JSON file
    
Examples:
    python test_training_dongle.py --duration 10
    python test_training_dongle.py --manager --export
    python test_training_dongle.py --calibrate
"""

import argparse
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any

# Add jetson-hardware to path
BASE_DIR = os.path.dirname(__file__)
JETSON_HW_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../jetson-hardware"))
if JETSON_HW_PATH not in sys.path:
    sys.path.insert(0, JETSON_HW_PATH)

try:
    from Libs.TrainingDongleLib import TrainingDongleLib, KeyEvent, TrainingScore
    from Managers.TrainingDongle_Manager import TrainingDongleManager
except ImportError as e:
    print(f"Error importing training dongle modules: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def test_device_detection():
    """Test basic device detection and info."""
    print("🔍 Testing Training Dongle Detection")
    print("=" * 50)
    
    dongle = TrainingDongleLib()
    device_info = dongle.get_device_info()
    
    print(f"Device Name: {device_info['device_name']}")
    print(f"Vendor ID: {device_info['vendor_id']}")
    print(f"Product ID: {device_info['product_id']}")
    print(f"Device Path: {device_info['device_path']}")
    print(f"Connected: {device_info['is_connected']}")
    print(f"Key Mapping: {device_info['key_mapping']}")
    
    return device_info['is_connected']


def test_direct_library(duration: float = 15.0, export_results: bool = False):
    """Test the training dongle using the direct library interface."""
    print(f"\n🧪 Testing Direct Library Interface ({duration}s)")
    print("=" * 50)
    
    dongle = TrainingDongleLib()
    
    if not dongle.device_path:
        print("❌ Training dongle not detected!")
        return False
    
    print("Press the 4 keys on your training dongle...")
    print("Key 1 = Excellent, Key 2 = Good, Key 3 = Poor, Key 4 = Failure")
    print("Golf-style scoring: Lower numbers = Better performance!")
    print(f"Testing for {duration} seconds...")
    
    results = dongle.test_device(duration)
    
    print(f"\n📊 Test Results:")
    print(f"Success: {results['success']}")
    print(f"Total Events: {results['total_events']}")
    print(f"Key Presses: {results['key_presses']}")
    print(f"Key Counts: {results['key_counts']}")
    
    if export_results:
        export_path = f"training_dongle_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_path, 'w') as f:
            # Make events serializable
            serializable_results = results.copy()
            serializable_results['events'] = [
                {
                    'key_number': e.key_number,
                    'score': e.score.name,
                    'timestamp': e.timestamp,
                    'event_type': e.event_type,
                    'raw_keycode': e.raw_keycode
                }
                for e in results['events']
            ]
            json.dump(serializable_results, f, indent=2)
        print(f"Results exported to: {export_path}")
    
    return results['success']


def test_manager_interface(duration: float = 15.0, export_results: bool = False):
    """Test the training dongle using the manager interface."""
    print(f"\n⚙️  Testing Manager Interface ({duration}s)")
    print("=" * 50)
    
    manager = TrainingDongleManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire training dongle manager!")
        return False
    
    try:
        device_info = manager.get_device_info()
        print(f"Manager Status: Acquired")
        print(f"Device Connected: {device_info['is_connected']}")
        
        # Test feedback monitoring
        feedback_events = []
        
        def on_feedback(event: KeyEvent):
            feedback_events.append(event)
            print(f"📝 Feedback: Key {event.key_number} ({event.score.name}) "
                  f"at {datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S.%f')[:-3]}")
        
        print("\nStarting feedback monitoring...")
        print("Press the 4 keys on your training dongle...")
        
        if not manager.start_feedback_monitoring(on_feedback):
            print("❌ Failed to start feedback monitoring!")
            return False
        
        # Monitor for specified duration
        start_time = time.time()
        while (time.time() - start_time) < duration:
            time.sleep(0.1)
        
        manager.stop_feedback_monitoring()
        
        # Get session statistics
        stats = manager.get_session_statistics()
        print(f"\n📊 Session Statistics:")
        print(f"Total Feedback: {stats['total_feedback']}")
        print(f"Average Score: {stats['average_score']:.2f} (golf-style: lower=better)")
        print(f"Score Distribution: {stats['score_counts']}")
        print(f"Feedback Rate: {stats['feedback_rate']:.2f} events/second")
        
        # Test recent feedback retrieval
        recent_feedback = manager.get_recent_feedback(30.0)
        print(f"Recent Feedback (30s): {len(recent_feedback)} events")
        
        if export_results:
            export_path = manager.export_feedback_data()
            print(f"Results exported to: {export_path}")
        
        return True
        
    finally:
        manager.release()


def calibrate_key_mapping():
    """Help discover the actual key mappings by testing each key individually."""
    print("\n🎯 Key Mapping Calibration")
    print("=" * 50)
    print("This will help discover which keycodes correspond to which physical keys.")
    print("You'll be prompted to press each key individually.\n")
    
    dongle = TrainingDongleLib()
    
    if not dongle.device_path:
        print("❌ Training dongle not detected!")
        return False
    
    discovered_mappings = {}
    
    for key_num in range(1, 5):
        input(f"Press ENTER when ready to test KEY {key_num}, then press and hold that key...")
        
        print(f"Monitoring for KEY {key_num} - press and hold the key now...")
        
        events = []
        def collect_event(event: KeyEvent):
            events.append(event)
            print(f"Detected: Keycode {event.raw_keycode} -> Key {event.key_number}")
        
        dongle.start_monitoring(collect_event)
        time.sleep(3.0)  # Give time to press the key
        dongle.stop_monitoring()
        
        if events:
            # Find the most common keycode for this key
            keycodes = [e.raw_keycode for e in events if e.event_type == "press"]
            if keycodes:
                most_common_keycode = max(set(keycodes), key=keycodes.count)
                discovered_mappings[most_common_keycode] = key_num
                print(f"✅ KEY {key_num} -> Keycode {most_common_keycode}")
            else:
                print(f"❌ No key presses detected for KEY {key_num}")
        else:
            print(f"❌ No events detected for KEY {key_num}")
        
        print()
    
    print("🎯 Discovered Key Mapping:")
    print(json.dumps(discovered_mappings, indent=2))
    
    # Save the mapping
    mapping_file = "discovered_key_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(discovered_mappings, f, indent=2)
    print(f"Mapping saved to: {mapping_file}")
    
    return discovered_mappings


def monitor_realtime_feedback(duration: float = 60.0):
    """Real-time feedback monitoring demonstration."""
    print(f"\n📡 Real-time Feedback Monitoring ({duration}s)")
    print("=" * 50)
    print("This demonstrates real-time feedback collection for robot training.")
    print("Imagine a robot is performing actions and you're scoring its performance.\n")
    
    manager = TrainingDongleManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire training dongle manager!")
        return False
    
    try:
        feedback_count = 0
        last_summary_time = time.time()
        
        def on_feedback(event: KeyEvent):
            nonlocal feedback_count
            feedback_count += 1
            
            # Simulate robot action context
            action_context = [
                "moving forward", "turning left", "backing up", "stopping",
                "picking up object", "avoiding obstacle", "following path"
            ][feedback_count % 7]
            
            print(f"🤖 Robot {action_context} -> "
                  f"👨‍🏫 Trainer: {event.score.name} (Key {event.key_number})")
        
        manager.start_feedback_monitoring(on_feedback)
        
        print("Robot is 'performing actions' - provide feedback using the 4 keys:")
        print("Key 1 = EXCELLENT 😍 (Amazing!)")
        print("Key 2 = GOOD      😊 (Nice job)")  
        print("Key 3 = POOR      😬 (Needs work)")
        print("Key 4 = FAILURE   💥 (Oh no!)")
        print("\nPress Ctrl+C to stop early\n")
        
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < duration:
                # Show periodic summary
                if time.time() - last_summary_time >= 10.0:
                    summary = manager.get_feedback_summary(timespan_minutes=1.0)
                    if summary['total_feedback'] > 0:
                        print(f"\n📊 Last minute: {summary['total_feedback']} feedback, "
                              f"avg score: {summary['average_score']:.1f}/4.0 (lower=better)")
                        print(f"Distribution: {summary['score_distribution']}\n")
                    last_summary_time = time.time()
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        manager.stop_feedback_monitoring()
        
        # Final statistics
        final_stats = manager.get_session_statistics()
        print(f"\n🏁 Final Statistics:")
        print(f"Session Duration: {final_stats['session_duration']:.1f}s")
        print(f"Total Feedback: {final_stats['total_feedback']}")
        print(f"Average Score: {final_stats['average_score']:.2f}/4.0 (golf-style: lower=better)")
        print(f"Feedback Rate: {final_stats['feedback_rate']:.2f} events/second")
        print(f"Score Distribution: {final_stats['score_counts']}")
        
        return True
        
    finally:
        manager.release()


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test 4-key USB training dongle")
    parser.add_argument("--duration", type=float, default=15.0,
                       help="Test duration in seconds (default: 15)")
    parser.add_argument("--manager", action="store_true",
                       help="Test manager interface instead of direct library")
    parser.add_argument("--calibrate", action="store_true",
                       help="Calibrate key mappings")
    parser.add_argument("--export", action="store_true",
                       help="Export test results to JSON")
    parser.add_argument("--realtime", action="store_true",
                       help="Run real-time feedback monitoring demo")
    
    args = parser.parse_args()
    
    print("🎹 Training Dongle Test Suite")
    print("=" * 50)
    
    # Check device detection first
    if not test_device_detection():
        print("\n❌ Training dongle not detected. Please check:")
        print("1. Device is plugged in")
        print("2. User has permissions (add to 'input' group or run with sudo)")
        print("3. Device is recognized by the system")
        return 1
    
    success = True
    
    if args.calibrate:
        calibrate_key_mapping()
    elif args.realtime:
        success = monitor_realtime_feedback(args.duration)
    elif args.manager:
        success = test_manager_interface(args.duration, args.export)
    else:
        success = test_direct_library(args.duration, args.export)
    
    if success:
        print("\n✅ Training dongle test completed successfully!")
        return 0
    else:
        print("\n❌ Training dongle test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())