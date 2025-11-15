#!/usr/bin/env python3
"""
demo_camera_manager.py

Interactive demo for Camera Manager showcasing USB camera capabilities.
Demonstrates real-time camera control and integration possibilities.

Usage:
    python3 SimpleTests/demo_camera_manager.py
"""

import sys
import time

sys.path.append('/home/phiip/workspace/jetson-hardware')

from Managers.Camera_Manager import CameraManager


def interactive_camera_demo():
    """Interactive camera demonstration."""
    print("🎥 Interactive Camera Manager Demo")
    print("=" * 40)
    
    manager = CameraManager()
    
    if not manager.acquire():
        print("❌ Failed to acquire camera manager")
        return
    
    try:
        # Discover cameras
        cameras = manager.list_cameras()
        
        if not cameras:
            print("❌ No cameras found!")
            return
        
        print("📷 Available Cameras:")
        for camera in cameras:
            print(f"  {camera['device_id']}: {camera['name']} ({camera['type']})")
        
        # Select camera
        if len(cameras) == 1:
            camera_id = cameras[0]['device_id']
            print(f"\n📷 Using camera {camera_id}")
        else:
            camera_id = int(input(f"\nSelect camera ID (0-{len(cameras)-1}): "))
        
        # Open camera
        print(f"\n🔧 Opening camera {camera_id}...")
        if not manager.open_camera(camera_id, width=640, height=480, fps=30):
            print("❌ Failed to open camera")
            return
        
        # Show camera info
        info = manager.get_camera_info()
        print(f"✅ Camera ready: {info['width']}x{info['height']} @ {info.get('actual_fps', 0):.1f}fps")
        
        while True:
            print("\n🎛️  Camera Demo Options:")
            print("1. Take a photo")
            print("2. Live preview (10 seconds)")
            print("3. Adjust camera properties")
            print("4. Camera info")
            print("5. Continuous capture test")
            print("0. Exit")
            
            try:
                choice = input("\nSelect option (0-5): ").strip()
                
                if choice == "0":
                    break
                    
                elif choice == "1":
                    # Take photo
                    timestamp = int(time.time())
                    filename = f"/tmp/camera_photo_{timestamp}.jpg"
                    
                    print("📸 Taking photo...")
                    if manager.save_image(filename):
                        print(f"✅ Photo saved to {filename}")
                    else:
                        print("❌ Failed to take photo")
                
                elif choice == "2":
                    # Live preview
                    print("🎥 Starting live preview (10 seconds, press 'q' to quit)...")
                    manager.show_live_preview("Camera Demo", max_duration=10)
                    print("✅ Live preview completed")
                
                elif choice == "3":
                    # Adjust properties
                    print("\n⚙️  Camera Properties:")
                    print("Available properties: brightness, contrast, saturation")
                    
                    prop = input("Property name: ").strip().lower()
                    if prop in ['brightness', 'contrast', 'saturation']:
                        try:
                            value = float(input(f"{prop.title()} value (0.0-1.0): "))
                            if 0.0 <= value <= 1.0:
                                if manager.set_camera_property(prop, value):
                                    print(f"✅ Set {prop} = {value}")
                                else:
                                    print(f"❌ Failed to set {prop}")
                            else:
                                print("❌ Value must be between 0.0 and 1.0")
                        except ValueError:
                            print("❌ Invalid value")
                    else:
                        print("❌ Unknown property")
                
                elif choice == "4":
                    # Camera info
                    info = manager.get_camera_info()
                    print("\n📊 Camera Information:")
                    print(f"  Status: {info.get('status', 'unknown')}")
                    print(f"  Resolution: {info.get('width', 0)}x{info.get('height', 0)}")
                    print(f"  FPS: {info.get('actual_fps', 0):.1f}")
                    print(f"  Frames captured: {info.get('total_frames', 0)}")
                    print(f"  Manager FPS: {info.get('manager_fps', 0):.1f}")
                
                elif choice == "5":
                    # Continuous capture test
                    print("\n🔄 Continuous capture test (30 frames)...")
                    
                    frame_count = 0
                    start_time = time.time()
                    
                    def capture_callback(frame, frame_info):
                        nonlocal frame_count
                        frame_count += 1
                        if frame_count % 10 == 0:
                            print(f"  Captured frame {frame_count}")
                    
                    manager.start_capture(capture_callback, max_frames=30)
                    time.sleep(2)  # Let it run
                    manager.stop_capture()
                    
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed if elapsed > 0 else 0
                    print(f"✅ Captured {frame_count} frames in {elapsed:.1f}s ({fps:.1f} FPS)")
                
                else:
                    print("❌ Invalid option")
                    
            except KeyboardInterrupt:
                print("\n👋 Demo interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Closing camera...")
        
    finally:
        manager.release()
        print("✅ Camera manager released")


def quick_camera_test():
    """Quick camera functionality test."""
    print("⚡ Quick Camera Test")
    print("-" * 20)
    
    manager = CameraManager()
    
    if not manager.acquire():
        print("❌ Could not acquire camera")
        return False
    
    try:
        # Quick test sequence
        cameras = manager.list_cameras()
        print(f"📷 Found {len(cameras)} cameras")
        
        if cameras:
            camera_id = cameras[0]['device_id']
            if manager.open_camera(camera_id):
                print(f"✅ Camera {camera_id} opened")
                
                frame = manager.capture_frame()
                if frame is not None:
                    print(f"✅ Frame captured: {frame.shape}")
                    return True
                else:
                    print("❌ No frame captured")
            else:
                print("❌ Could not open camera")
        else:
            print("❌ No cameras available")
        
        return False
        
    finally:
        manager.release()


def main():
    """Main demo entry point."""
    print("🚀 Camera Manager Demo Suite")
    print("🎥 USB Camera Control for Jetson Orin Nano")
    print("=" * 50)
    
    # Quick test first
    print("Running quick connectivity test...")
    if not quick_camera_test():
        print("\n❌ Quick test failed!")
        print("💡 Check:")
        print("   - USB camera is connected")
        print("   - Camera permissions (try: sudo usermod -a -G video $USER)")
        print("   - No other applications using the camera")
        return
    
    print("\n✅ Quick test passed! Camera is working.")
    
    # Ask for full demo
    response = input("\nRun full interactive demo? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        interactive_camera_demo()
    else:
        print("👋 Demo complete!")


if __name__ == "__main__":
    main()
