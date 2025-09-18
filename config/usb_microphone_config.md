# USB Microphone Configuration for Jetson Orin Nano

## Verified Working Configuration

This documents the confirmed working USB microphone setup for the StreamingMicManager to avoid future debugging sessions.

### Hardware Details

**USB Audio Device**: Generic USB microphones
- **ALSA Device**: `hw:0,0` (USB Audio Device: -)  
- **Sample Rate**: 44100 Hz (auto-detected)
- **Format**: S16_LE (16-bit signed little-endian)
- **Channels**: 1 (mono)
- **Chunk Size**: 1024 samples (optimized for real-time)

### Detection Status

**Auto-detection Working**: ✅ The StreamingMicManager automatically finds and configures USB microphones.

**Detection Method**:
1. Scans `/proc/asound/cards` for USB audio devices
2. Tests sample rates: [44100, 48000, 16000] Hz
3. Selects best working configuration
4. Logs device info for troubleshooting

### Verification Commands

To verify your USB microphone is detected properly:

```bash
# Check available sound cards
cat /proc/asound/cards

# Expected output should include:
# 0 [Device         ]: USB-Audio - USB Audio Device
#                      USB Audio Device at usb-...

# List recording devices  
arecord -l

# Expected output:
# card 0: Device [USB Audio Device], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
#   Subdevice #0: subdevice #0

# Test recording (Ctrl+C to stop)
arecord -D hw:0,0 -f S16_LE -r 44100 -c 1 -t wav test.wav

# Test playback
aplay test.wav
```

### StreamingMicManager Configuration

**No configuration needed!** The StreamingMicManager automatically:

```python
from Managers.Mic_Manager_Streaming import StreamingMicManager

# This automatically detects and configures USB microphone
mic = StreamingMicManager()
mic.acquire()

# The system will log detection info like:
# [USB MIC] Found device 0: USB Audio Device: - (hw:0,0) at 44100Hz
```

### Calibrated Thresholds

**Typical Values** (auto-calibrated on startup):
- **Background noise**: 0.3 - 0.5
- **Speech start threshold**: 15 - 25  
- **Speech continue threshold**: 6 - 10
- **Normal speech amplitude**: 20 - 100
- **Loud speech amplitude**: 100 - 500

**Calibration Process**:
1. 3 seconds of silence measurement
2. Threshold = background + (background * 20 + 10)
3. Hysteresis = start_threshold * 0.4

### Performance Characteristics

**Confirmed Performance** (measured on Jetson Orin Nano):
- **Voice detection latency**: <50ms from speech start
- **Audio processing**: 5-10ms per chunk
- **STT processing**: 300-800ms (with jetson-stt tiny.en model)
- **Total command response**: 0.3-0.8 seconds

### Troubleshooting

**If USB microphone not detected:**

1. **Check USB connection**:
   ```bash
   lsusb | grep -i audio
   ```

2. **Check ALSA recognition**:
   ```bash
   cat /proc/asound/cards
   ```

3. **Check permissions**:
   ```bash
   groups $USER  # Should include 'audio'
   ```

4. **Restart ALSA if needed**:
   ```bash
   sudo alsa force-reload
   ```

5. **Test with debug script**:
   ```bash
   cd /home/phiip/Agents/Zig_Zag
   python debug_usb_mic.py
   ```

**If audio levels are wrong:**

1. **Adjust system levels**:
   ```bash
   alsamixer
   # Press F6 to select USB Audio Device
   # Adjust microphone levels
   ```

2. **Check for mute**:
   ```bash
   amixer sget Capture
   amixer sset Capture unmute
   ```

**If thresholds need manual adjustment:**

```python
mic = StreamingMicManager()
mic.acquire()

# Skip auto-calibration and set manual thresholds
mic.start_voice_detection(
    start_speech_threshold=20.0,     # Manual start threshold
    continue_speech_threshold=8.0,   # Manual continue threshold
    callback=your_callback
)
```

### Integration Examples

**Quick test**:
```bash
cd /home/phiip/Agents/Zig_Zag
python demo_realtime_stt.py
```

**Real-time voice control**:
```bash
cd /home/phiip/Agents/Zig_Zag  
python zig_zag_realtime.py
```

### Future Hardware Notes

When adding new USB microphones:
1. Test with `debug_usb_mic.py` first
2. Verify `arecord -l` shows the device
3. Check auto-detection logs in StreamingMicManager
4. Document any special configuration needed here

### Last Updated

**Date**: September 18, 2025
**Verified on**: Jetson Orin Nano with USB Audio Device
**Software**: StreamingMicManager v1.0, ALSA 1.2.x