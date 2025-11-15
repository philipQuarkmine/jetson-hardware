#!/usr/bin/env python3
"""
test_camera_manager.py

Test script for Camera Manager with USB camera support.
Demonstrates camera discovery, capture, and live preview capabilities.

Usage:
    python3 SimpleTests/test_camera_manager.py
"""

import sys
import time

sys.path.append('/home/phiip/workspace/jetson-hardware')

import cv2

from Managers.Camera_Manager import CameraManager


def test_camera_discovery():
    """Test camera discovery functionality."""
    print("🔍 Testing Camera Discovery...")
    
    manager = CameraManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    try:
        # List available cameras
        cameras = manager.list_cameras()
        print(f"📷 Found {len(cameras)} cameras:")
        
        for camera in cameras:
            print(f"  Camera {camera['device_id']}: {camera['name']}")
            print(f"    Type: {camera['type']}")
            print(f"    Resolutions: {camera['supported_resolutions']}")
            print(f"    Formats: {camera['supported_formats']}")
            print()
        
        return len(cameras) > 0
        
    finally:
        manager.release()


def test_camera_capture():
    """Test basic camera capture functionality."""
    print("📸 Testing Camera Capture...")
    
    manager = CameraManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    try:
        # Open camera
        print("📷 Opening camera 0 at 640x480...")
        if not manager.open_camera(camera_id=0, width=640, height=480, fps=30):
            print("❌ Failed to open camera")
            return False
        
        # Get camera info
        info = manager.get_camera_info()
        print(f"✅ Camera opened: {info['width']}x{info['height']} @ {info['fps']:.1f}fps")
        
        # Capture a few frames
        print("📸 Capturing frames...")
        for i in range(5):
            frame = manager.capture_frame()
            if frame is not None:
                print(f"  Frame {i+1}: {frame.shape}")
            else:
                print(f"  Frame {i+1}: Failed to capture")
            time.sleep(0.1)
        
        # Save a test image
        print("💾 Saving test image...")
        timestamp = int(time.time())
        filename = f"/tmp/test_camera_{timestamp}.jpg"
        
        if manager.save_image(filename):
            print(f"✅ Image saved to {filename}")
        else:
            print("❌ Failed to save image")
        
        return True
        
    finally:
        manager.release()


def test_live_preview():
    """Test live camera preview."""
    print("🎥 Testing Live Preview...")
    print("📺 Live preview will open for 10 seconds (press 'q' to quit early)")
    
    manager = CameraManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    try:
        # Open camera
        if not manager.open_camera(camera_id=0, width=640, height=480, fps=30):
            print("❌ Failed to open camera")
            return False
        
        # Show live preview
        success = manager.show_live_preview("USB Camera Test", max_duration=10)
        
        if success:
            print("✅ Live preview completed")
        else:
            print("❌ Live preview failed")
        
        return success
        
    finally:
        manager.release()


def test_continuous_capture():
    """Test continuous capture with callback."""
    print("🔄 Testing Continuous Capture...")
    
    manager = CameraManager()
    frame_count = 0
    fps_sum = 0.0
    
    def frame_callback(frame, frame_info):
        """Process each captured frame."""
        nonlocal frame_count, fps_sum
        frame_count += 1
        fps_sum += frame_info.get('manager_fps', 0)
        
        if frame_count % 10 == 0:  # Print every 10th frame
            avg_fps = fps_sum / frame_count if frame_count > 0 else 0
            print(f"  Frame {frame_count}: {frame.shape}, avg FPS: {avg_fps:.1f}")
    
    if not manager.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    try:
        # Open camera
        if not manager.open_camera(camera_id=0, width=640, height=480, fps=30):
            print("❌ Failed to open camera")
            return False
        
        # Start continuous capture
        print("🎬 Starting continuous capture for 50 frames...")
        if not manager.start_capture(frame_callback, max_frames=50):
            print("❌ Failed to start capture")
            return False
        
        # Wait for capture to complete
        time.sleep(3)  # Give some time for capture
        
        # Stop capture
        manager.stop_capture()
        
        avg_fps = fps_sum / frame_count if frame_count > 0 else 0
        print(f"✅ Captured {frame_count} frames, avg FPS: {avg_fps:.1f}")
        
        return frame_count > 0
        
    finally:
        manager.release()


def test_camera_properties():
    """Test camera property adjustment."""
    print("⚙️  Testing Camera Properties...")
    
    manager = CameraManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    try:
        # Open camera
        if not manager.open_camera(camera_id=0, width=640, height=480):
            print("❌ Failed to open camera")
            return False
        
        # Test setting properties
        properties = {
            'brightness': 0.6,
            'contrast': 0.7,
            'saturation': 0.5
        }
        
        for prop_name, value in properties.items():
            success = manager.set_camera_property(prop_name, value)
            if success:
                print(f"✅ Set {prop_name} = {value}")
            else:
                print(f"⚠️  Could not set {prop_name} (may not be supported)")
        
        # Capture a frame to see the effect
        frame = manager.capture_frame()
        if frame is not None:
            print(f"✅ Captured frame with adjusted properties: {frame.shape}")
            return True
        else:
            print("❌ Failed to capture frame with properties")
            return False
        
    finally:
        manager.release()


def main():
    """Run all camera manager tests."""
    print("🚀 Camera Manager Test Suite")
    print("=" * 50)
    
    tests = [
        ("Camera Discovery", test_camera_discovery),
        ("Basic Capture", test_camera_capture),
        ("Continuous Capture", test_continuous_capture),
        ("Camera Properties", test_camera_properties),
        ("Live Preview", test_live_preview),  # Interactive test last
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Camera Manager is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check camera connection and permissions.")


if __name__ == "__main__":
    main()
