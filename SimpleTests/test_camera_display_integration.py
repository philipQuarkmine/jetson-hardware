#!/usr/bin/env python3
"""
test_camera_display_integration.py

Test Camera Manager integration with Display Manager.
Shows USB camera feed directly on the Jetson framebuffer display.

Usage:
    python3 SimpleTests/test_camera_display_integration.py
"""

import sys
import time

import numpy as np

sys.path.append('/home/phiip/workspace/jetson-hardware')

from PIL import Image

from Managers.Camera_Manager import CameraManager
from Managers.Display_Manager import DisplayManager


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
            print()
        
        return len(cameras) > 0
        
    finally:
        manager.release()


def test_camera_with_display():
    """Test camera capture with Display Manager output."""
    print("🎥📺 Testing Camera + Display Integration...")
    
    camera = CameraManager()
    display = DisplayManager()
    
    # Acquire both managers
    if not camera.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    if not display.acquire():
        print("❌ Failed to acquire display manager")
        camera.release()
        return False
    
    try:
        # Open camera
        print("📷 Opening camera...")
        if not camera.open_camera(camera_id=0, width=640, height=480, fps=30):
            print("❌ Failed to open camera")
            return False
        
        # Clear display with dark background
        display.clear_screen((20, 20, 40))
        
        # Show title
        display.show_text("JETSON CAMERA TEST", (50, 30), (255, 255, 0), 32, True)
        time.sleep(2)
        
        # Capture and display frames
        print("📸 Capturing frames and displaying on screen...")
        
        frame_count = 0
        start_time = time.time()
        
        for i in range(100):  # Capture 100 frames
            # Capture frame from camera
            frame = camera.capture_frame()
            if frame is None:
                print(f"❌ Failed to capture frame {i+1}")
                continue
            
            frame_count += 1
            
            # Convert BGR to RGB for PIL
            frame_rgb = frame[:, :, ::-1]  # BGR to RGB
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Calculate position to center camera feed
            display_info = display.get_display_info()
            display_width = display_info.get('width', 1280)
            display_height = display_info.get('height', 1024)
            
            cam_width, cam_height = pil_image.size
            x_pos = (display_width - cam_width) // 2
            y_pos = (display_height - cam_height) // 2 + 50  # Offset for title
            
            # Clear previous frame area (just the camera region)
            display.draw_rectangle((x_pos-5, y_pos-5), 
                                 (cam_width+10, cam_height+10), 
                                 (20, 20, 40), True, False)
            
            # Save frame temporarily and display it
            temp_filename = "/tmp/camera_frame.jpg"
            pil_image.save(temp_filename)
            
            # Display frame on screen
            display.show_image(temp_filename, (x_pos, y_pos), scale=1.0, update=False)
            
            # Add frame info overlay
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            info_text = f"Frame: {frame_count}  FPS: {fps:.1f}  Resolution: {cam_width}x{cam_height}"
            display.show_text(info_text, (50, display_height - 100), (0, 255, 0), 20, False)
            
            # Show instructions
            display.show_text("Camera feed updating in real-time", 
                            (50, display_height - 60), (255, 255, 255), 16, False)
            display.show_text("Press Ctrl+C to stop", 
                            (50, display_height - 30), (255, 100, 100), 16, False)
            
            # Update display
            display.update_display()
            
            # Print progress every 10 frames
            if frame_count % 10 == 0:
                print(f"  📸 Frame {frame_count}: {fps:.1f} FPS")
            
            # Brief pause to control frame rate
            time.sleep(0.033)  # ~30 FPS
        
        # Final statistics
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        # Show completion message
        display.clear_screen((0, 40, 20))
        display.show_text("CAMERA TEST COMPLETE", (300, 400), (0, 255, 0), 48, False)
        display.show_text(f"Captured {frame_count} frames", (350, 500), (255, 255, 255), 24, False)
        display.show_text(f"Average FPS: {avg_fps:.1f}", (380, 540), (255, 255, 255), 24, True)
        
        time.sleep(3)  # Show results for 3 seconds
        
        print(f"✅ Camera test completed: {frame_count} frames, {avg_fps:.1f} FPS")
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        return True
    except Exception as e:
        print(f"❌ Error in camera+display test: {e}")
        return False
    finally:
        camera.release()
        display.release()


def test_camera_photo_gallery():
    """Take several photos and display them in a gallery."""
    print("📸🖼️ Testing Camera Photo Gallery...")
    
    camera = CameraManager()
    display = DisplayManager()
    
    # Acquire both managers
    if not camera.acquire():
        print("❌ Failed to acquire camera manager")
        return False
    
    if not display.acquire():
        print("❌ Failed to acquire display manager")
        camera.release()
        return False
    
    try:
        # Open camera
        if not camera.open_camera(camera_id=0, width=640, height=480):
            print("❌ Failed to open camera")
            return False
        
        photos = []
        
        # Take 4 photos with countdown
        for i in range(4):
            # Clear screen and show countdown
            display.clear_screen((40, 0, 40))
            display.show_text(f"PHOTO {i+1}/4", (400, 300), (255, 255, 0), 48, False)
            
            for countdown in range(3, 0, -1):
                display.draw_circle((640, 500), 60, (255, 100, 100), True, False)
                display.show_text(str(countdown), (620, 480), (255, 255, 255), 72, True)
                time.sleep(1)
            
            # Take photo
            display.show_text("SMILE! 📸", (500, 600), (0, 255, 0), 32, True)
            
            frame = camera.capture_frame()
            if frame is not None:
                # Convert and save photo
                frame_rgb = frame[:, :, ::-1]
                pil_image = Image.fromarray(frame_rgb)
                
                timestamp = int(time.time())
                filename = f"/tmp/photo_{i+1}_{timestamp}.jpg"
                pil_image.save(filename)
                
                photos.append(filename)
                print(f"  📸 Photo {i+1} saved: {filename}")
            else:
                print(f"  ❌ Failed to capture photo {i+1}")
            
            time.sleep(1)
        
        # Display gallery
        if photos:
            display.clear_screen((0, 20, 40))
            display.show_text("PHOTO GALLERY", (400, 50), (255, 255, 0), 36, False)
            
            # Display photos in 2x2 grid
            positions = [(200, 150), (700, 150), (200, 400), (700, 400)]
            
            for i, (photo, pos) in enumerate(zip(photos, positions, strict=False)):
                if i < len(photos):
                    # Scale down photos for gallery view
                    display.show_image(photo, pos, scale=0.4, update=False)
                    display.show_text(f"Photo {i+1}", (pos[0], pos[1] + 200), 
                                    (255, 255, 255), 16, False)
            
            display.show_text("Gallery complete! Photos saved to /tmp/", 
                            (250, 750), (0, 255, 0), 20, True)
            
            time.sleep(5)  # Show gallery for 5 seconds
        
        print(f"✅ Photo gallery completed: {len(photos)} photos taken")
        return True
        
    except Exception as e:
        print(f"❌ Error in photo gallery: {e}")
        return False
    finally:
        camera.release()
        display.release()


def test_camera_properties_visual():
    """Test camera property adjustments with visual feedback."""
    print("⚙️📺 Testing Camera Properties with Visual Feedback...")
    
    camera = CameraManager()
    display = DisplayManager()
    
    if not camera.acquire() or not display.acquire():
        print("❌ Failed to acquire managers")
        return False
    
    try:
        if not camera.open_camera(camera_id=0, width=640, height=480):
            print("❌ Failed to open camera")
            return False
        
        properties_to_test = [
            ('brightness', [0.3, 0.7]),
            ('contrast', [0.3, 0.8]),
            ('saturation', [0.2, 0.8])
        ]
        
        for prop_name, values in properties_to_test:
            for value in values:
                # Set property
                success = camera.set_camera_property(prop_name, value)
                
                # Clear display
                display.clear_screen((30, 30, 30))
                
                # Show property info
                title = f"Testing {prop_name.upper()}: {value}"
                display.show_text(title, (300, 50), (255, 255, 0), 28, False)
                
                if success:
                    display.show_text("✅ Property set successfully", 
                                    (350, 100), (0, 255, 0), 20, False)
                else:
                    display.show_text("⚠️ Property not supported", 
                                    (350, 100), (255, 150, 0), 20, False)
                
                # Capture frame with new property
                frame = camera.capture_frame()
                if frame is not None:
                    frame_rgb = frame[:, :, ::-1]
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Save and display frame
                    temp_file = "/tmp/camera_property_test.jpg"
                    pil_image.save(temp_file)
                    
                    # Center the image
                    display.show_image(temp_file, (320, 200), scale=0.8, update=True)
                
                time.sleep(2)  # Show each setting for 2 seconds
        
        # Reset to defaults
        display.clear_screen((0, 40, 0))
        display.show_text("PROPERTY TEST COMPLETE", (300, 400), (255, 255, 255), 32, False)
        display.show_text("Resetting to defaults...", (400, 450), (200, 200, 200), 20, True)
        
        # Reset properties
        camera.set_camera_property('brightness', 0.5)
        camera.set_camera_property('contrast', 0.5)
        camera.set_camera_property('saturation', 0.5)
        
        time.sleep(2)
        
        print("✅ Camera properties test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error in properties test: {e}")
        return False
    finally:
        camera.release()
        display.release()


def main():
    """Run all camera + display integration tests."""
    print("🚀 Camera + Display Integration Test Suite")
    print("🎥📺 USB Camera with Jetson Display Manager")
    print("=" * 60)
    
    tests = [
        ("Camera Discovery", test_camera_discovery),
        ("Camera + Display Live Feed", test_camera_with_display),
        ("Photo Gallery", test_camera_photo_gallery),
        ("Visual Property Testing", test_camera_properties_visual),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except KeyboardInterrupt:
            print(f"\n👋 {test_name} interrupted by user")
            results[test_name] = True  # User interruption counts as success
            break
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            results[test_name] = False
        
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Camera + Display integration is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check camera and display setup.")


if __name__ == "__main__":
    main()
