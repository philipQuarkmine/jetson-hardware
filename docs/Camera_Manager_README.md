# Camera Manager Documentation

## Overview

The Camera Manager provides thread-safe access to USB cameras on the Jetson Orin Nano, with seamless integration with the Display Manager for real-time visual feedback.

## Features

- ✅ **USB Camera Support**: Full support for USB 2.0 cameras with auto-discovery
- ✅ **Thread-Safe Access**: Acquire/release pattern with file locking
- ✅ **Display Integration**: Direct integration with Display Manager for real-time preview
- ✅ **Multiple Resolutions**: Support for 320x240, 640x480, and higher resolutions
- ✅ **Property Control**: Brightness, contrast, saturation adjustment
- ✅ **Photo Capture**: Single frame and continuous capture modes
- ✅ **Performance Monitoring**: Real-time FPS tracking and statistics
- 🔄 **Future Ready**: Architecture designed for IMX708 CSI camera support

## Architecture

### Current Implementation
```
CameraManager -> CameraLib -> OpenCV -> USB Camera (/dev/video0)
     ↓
DisplayManager -> DisplayLib -> Framebuffer (/dev/fb0)
```

### Future Architecture (IMX708 Support)
```
CameraManager -> CameraLib -> Backend Selection:
                                ├── OpenCV (USB cameras)
                                └── GStreamer/libcamera (CSI cameras)
```

## Basic Usage

### Simple Photo Capture
```python
from Managers.Camera_Manager import CameraManager

# Initialize and acquire camera
camera = CameraManager()
camera.acquire()

# Open camera at 640x480
camera.open_camera(camera_id=0, width=640, height=480, fps=30)

# Take a photo
frame = camera.capture_frame()
camera.save_image("/tmp/photo.jpg", frame)

# Cleanup
camera.release()
```

### Camera Discovery
```python
# Find available cameras
camera = CameraManager()
camera.acquire()

cameras = camera.list_cameras()
for cam in cameras:
    print(f"Camera {cam['device_id']}: {cam['name']}")
    print(f"  Resolutions: {cam['supported_resolutions']}")

camera.release()
```

### Real-Time Display Integration
```python
from Managers.Camera_Manager import CameraManager
from Managers.Display_Manager import DisplayManager

camera = CameraManager()
display = DisplayManager()

# Acquire both managers
camera.acquire()
display.acquire()

try:
    # Open camera and display
    camera.open_camera(camera_id=0, width=640, height=480)
    
    # Capture and display frames
    for i in range(100):
        frame = camera.capture_frame()
        if frame is not None:
            # Convert BGR to RGB for PIL
            frame_rgb = frame[:, :, ::-1]
            pil_image = Image.fromarray(frame_rgb)
            
            # Save temporarily and display
            pil_image.save("/tmp/live_frame.jpg")
            display.show_image("/tmp/live_frame.jpg", (320, 200), update=True)

finally:
    camera.release()
    display.release()
```

### Continuous Capture with Callback
```python
def process_frame(frame, frame_info):
    """Process each captured frame."""
    print(f"Frame {frame_info['frame_number']}: "
          f"{frame_info['width']}x{frame_info['height']} "
          f"@ {frame_info['fps']:.1f} FPS")

camera = CameraManager()
camera.acquire()
camera.open_camera(camera_id=0)

# Start continuous capture
camera.start_capture(process_frame, max_frames=100)

# Stop when done
camera.stop_capture()
camera.release()
```

## Camera Properties

Adjust camera settings for optimal image quality:

```python
# Brightness (0.0 = darkest, 1.0 = brightest)
camera.set_camera_property('brightness', 0.7)

# Contrast (0.0 = no contrast, 1.0 = maximum contrast)
camera.set_camera_property('contrast', 0.6)

# Saturation (0.0 = grayscale, 1.0 = full color)
camera.set_camera_property('saturation', 0.8)
```

## Supported Camera Formats

### Current USB Camera Support
- **Format**: YUYV 4:2:2
- **Resolutions**: 
  - 320x240 @ 30 FPS
  - 640x480 @ 30 FPS
- **Device**: `/dev/video0` (USB 2.0 CAMERA)

### Future CSI Camera Support (IMX708)
- **Format**: Various (RGB, BAYER, etc.)
- **Resolutions**: Up to 4056x3040
- **Interface**: CSI via `/dev/media0`

## Testing

### Quick Test
```bash
cd /home/phiip/workspace/jetson-hardware
python3 SimpleTests/test_camera_display_integration.py
```

### Interactive Demo
```bash
python3 SimpleTests/demo_camera_manager.py
```

## Performance

### Measured Performance (USB 2.0 Camera)
- **Capture Rate**: ~7.6 FPS sustained
- **Display Rate**: Real-time with Display Manager
- **Resolution**: 640x480 optimal for real-time use
- **Memory Usage**: ~50MB for camera + display operations

### Optimization Tips
1. **Lower resolution** for higher FPS (320x240 → ~15+ FPS)
2. **Buffer management** for continuous capture
3. **Display scaling** to reduce framebuffer operations
4. **Threading** for capture + processing separation

## Error Handling

The Camera Manager provides robust error handling:

```python
try:
    camera = CameraManager()
    if not camera.acquire():
        print("Camera busy or permission denied")
        return
    
    if not camera.open_camera(camera_id=0):
        print("Camera not available or in use")
        return
    
    # Camera operations...
    
except Exception as e:
    print(f"Camera error: {e}")
finally:
    camera.release()  # Always cleanup
```

## Common Issues

### Camera Not Found
- Check USB connection
- Verify permissions: `sudo usermod -a -G video $USER`
- Check if other applications are using camera

### Low FPS Performance
- Reduce resolution: Use 320x240 for higher FPS
- Check system load: `htop` to monitor CPU usage
- Optimize display operations: Use lower scale factors

### Display Integration Issues
- Ensure Display Manager is working: Test with `test_display_manager.py`
- Check framebuffer permissions: `/dev/fb0` should be accessible
- Verify PIL installation for image conversion

## Future Enhancements

### Planned Features
- ✨ **IMX708 CSI Camera Support**: High-resolution CSI camera integration
- ✨ **GStreamer Backend**: Hardware-accelerated camera pipeline  
- ✨ **Multi-Camera**: Simultaneous USB + CSI camera operation
- ✨ **Video Recording**: MP4/H.264 video capture with hardware encoding
- ✨ **Auto-Exposure**: Advanced camera control algorithms
- ✨ **Zoom & Pan**: Digital zoom and pan functionality

### Backend Selection Architecture
```python
# Future API design
camera = CameraManager(backend='auto')  # Auto-detect best backend
camera = CameraManager(backend='usb')   # Force USB/OpenCV
camera = CameraManager(backend='csi')   # Force CSI/GStreamer
```

---

**The Camera Manager provides a solid foundation for robotics vision applications on the Jetson Orin Nano, with seamless integration into the jetson-hardware ecosystem.**