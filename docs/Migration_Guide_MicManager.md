# Migration Guide: MicManager to StreamingMicManager

## Overview

This guide helps you migrate from the legacy `MicManager` to the new `StreamingMicManager` for real-time voice applications. The streaming version provides sub-second latency and automatic voice activity detection.

## When to Use Which Manager

### Use StreamingMicManager for:
- Real-time voice control systems
- Voice command interfaces requiring <1s response time
- Applications needing automatic speech detection
- Robot control with voice commands
- Interactive voice applications

### Use Legacy MicManager for:
- Scheduled recordings
- Batch audio processing
- Simple "record on demand" functionality
- Background monitoring (like LED sound monitor)

## Migration Examples

### Example 1: Voice Command System

**Before (Legacy MicManager):**
```python
from Managers.Mic_Manager import MicManager

mic = MicManager()
mic.acquire()

try:
    # Manual recording
    audio_file = mic.record(duration=5, filename="command.wav")
    # Process file with STT...
finally:
    mic.release()
```

**After (StreamingMicManager):**
```python
from Managers.Mic_Manager_Streaming import StreamingMicManager

mic = StreamingMicManager()
mic.acquire()

def process_speech(audio_data, sample_rate):
    # Real-time processing with audio data directly
    # No file I/O needed!
    print(f"Speech: {len(audio_data)} samples at {sample_rate}Hz")

try:
    mic.start_voice_detection(
        callback=process_speech,
        min_speech_duration=0.3,
        max_silence_duration=1.0
    )
    # System automatically detects speech and calls callback
    input("Press Enter to stop...")
finally:
    mic.stop_voice_detection()
    mic.release()
```

### Example 2: Robot Voice Control Integration

**Complete integration with STT:**
```python
import sys
sys.path.append('/home/phiip/jetson-hardware')
sys.path.append('/home/phiip/jetson-stt')

from Managers.Mic_Manager_Streaming import StreamingMicManager
from stt_streaming import StreamingJetsonSTT

class VoiceRobotController:
    def __init__(self):
        self.mic = StreamingMicManager()
        self.stt = StreamingJetsonSTT()
        
    def run(self):
        self.mic.acquire()
        
        def handle_voice_command(audio_data, sample_rate):
            # Convert speech to text
            result = self.stt.transcribe_audio_data(audio_data, sample_rate)
            command = result.get('text', '').strip()
            
            # Process command
            if 'stop' in command.lower():
                print("🛑 Stop command detected!")
                # Execute stop logic
            elif 'forward' in command.lower():
                print("⬆️ Move forward!")
                # Execute forward logic
        
        try:
            self.mic.start_voice_detection(
                callback=handle_voice_command,
                min_speech_duration=0.3,    # Quick commands
                max_silence_duration=1.0,   # Fast cutoff
                pre_recording_duration=0.5  # Catch wake words
            )
            
            print("Voice control active. Say 'Hey robot, go forward' or 'Stop'")
            input("Press Enter to stop...")
            
        finally:
            self.mic.stop_voice_detection()
            self.mic.release()

# Run the controller
controller = VoiceRobotController()
controller.run()
```

## Hardware Configuration Changes

### Automatic USB Detection

The new StreamingMicManager automatically detects USB microphones:

```python
# Old way - manual device specification
mic = MicManager(audio_device='plughw:0,0')

# New way - automatic detection
mic = StreamingMicManager()  # Finds USB mic automatically
```

### Sample Rate Handling

```python
# Old way - assumed 16kHz
mic = MicManager()

# New way - auto-detects device capabilities
mic = StreamingMicManager()  # Detects 44100Hz USB mics automatically
```

## API Differences

### Recording Interface

| Legacy MicManager | StreamingMicManager |
|------------------|---------------------|
| `record(duration, filename)` | `start_voice_detection(callback)` |
| Returns file path | Calls callback with audio data |
| File-based | Memory-based (faster) |
| Manual timing | Automatic speech detection |

### Audio Access

| Legacy | Streaming |
|--------|-----------|
| `get_sound_level(duration)` | Real-time amplitude in callback |
| Blocking call | Non-blocking with callbacks |
| Average over duration | Continuous monitoring |

## Configuration Migration

### Timing Parameters

```python
# Legacy: Fixed recording duration
mic.record(duration=5)

# Streaming: Configurable speech detection
mic.start_voice_detection(
    min_speech_duration=0.3,     # Minimum speech length
    max_silence_duration=1.0,    # When to end detection
    max_recording_duration=8.0   # Maximum total length
)
```

### Threshold Configuration

```python
# Legacy: Manual threshold in get_sound_level()
amplitude = mic.get_sound_level(threshold=500)

# Streaming: Auto-calibrating thresholds
mic.calibrate_noise_floor()  # Automatic
mic.start_voice_detection()  # Uses calibrated thresholds
```

## Files That Need Migration

### Confirmed Files Using Legacy MicManager:

1. **`/home/phiip/jetson-hardware/led_sound_monitor.py`**
   - Current use: LED brightness based on audio levels
   - Recommendation: Keep legacy for this use case (background monitoring)

2. **`/home/phiip/Agents/Zig_Zag/zig_zag.py`**
   - Current use: Voice command recording with manual triggers
   - Recommendation: **Migrate to StreamingMicManager** for better user experience

### Files Already Using StreamingMicManager:

1. **`/home/phiip/Agents/Zig_Zag/zig_zag_realtime.py`** ✅
2. **`/home/phiip/Agents/Zig_Zag/demo_realtime_stt.py`** ✅

## Performance Comparison

| Feature | Legacy MicManager | StreamingMicManager |
|---------|------------------|---------------------|
| Latency | 2-5 seconds | 0.3-0.8 seconds |
| Voice Detection | Manual | Automatic |
| USB Support | Manual config | Auto-detection |
| Real-time Processing | No | Yes |
| File I/O | Required | Optional |
| Memory Usage | Low | Moderate |
| CPU Usage | Low | Moderate |

## Troubleshooting Migration

### Common Issues

1. **Import Errors**
   ```python
   # Wrong
   from Managers.Mic_Manager import MicManager
   
   # Correct
   from Managers.Mic_Manager_Streaming import StreamingMicManager
   ```

2. **Callback vs File-based Processing**
   ```python
   # Old pattern
   audio_file = mic.record(5)
   # process file...
   
   # New pattern
   def process_audio(audio_data, sample_rate):
       # process audio_data directly
   mic.start_voice_detection(callback=process_audio)
   ```

3. **Threading Considerations**
   ```python
   # Streaming manager uses background threads
   # Always call stop_voice_detection() before release()
   mic.start_voice_detection(callback=my_callback)
   # ... app runs ...
   mic.stop_voice_detection()  # Important!
   mic.release()
   ```

### Hardware Issues

1. **USB Microphone Not Detected**
   ```bash
   # Check available devices
   cat /proc/asound/cards
   arecord -l
   
   # Test microphone
   arecord -D hw:0,0 -f S16_LE -r 44100 -c 1 -t wav test.wav
   ```

2. **Audio Levels Too Low/High**
   ```bash
   # Adjust system audio levels
   alsamixer
   # Use F6 to select USB audio device
   ```

## Testing Your Migration

Use the provided test script to verify your migration:

```bash
cd /home/phiip/Agents/Zig_Zag
python demo_realtime_stt.py
```

This will show:
- USB microphone detection
- Automatic threshold calibration
- Real-time voice activity detection
- STT processing times

## Future-Proofing

### Best Practices

1. **Always use try/finally blocks:**
   ```python
   mic = StreamingMicManager()
   mic.acquire()
   try:
       # Your voice processing
   finally:
       mic.stop_voice_detection()
       mic.release()
   ```

2. **Handle callback exceptions:**
   ```python
   def safe_callback(audio_data, sample_rate):
       try:
           # Your processing
       except Exception as e:
           print(f"Processing error: {e}")
   ```

3. **Use appropriate timeout settings:**
   ```python
   # For commands (fast response)
   mic.start_voice_detection(
       max_silence_duration=1.0,
       min_speech_duration=0.3
   )
   
   # For conversations (natural pauses)
   mic.start_voice_detection(
       max_silence_duration=2.0,
       min_speech_duration=0.5
   )
   ```

## Getting Help

- **Documentation**: `/home/phiip/jetson-hardware/docs/Streaming_Mic_Manager_README.md`
- **Examples**: `/home/phiip/Agents/Zig_Zag/demo_realtime_stt.py`
- **Debug Tools**: `/home/phiip/Agents/Zig_Zag/debug_usb_mic.py`

## Summary

The new StreamingMicManager provides significant improvements for real-time voice applications:

- **5-10x faster response times** (0.3-0.8s vs 2-5s)
- **Automatic speech detection** (no manual triggers needed)
- **USB microphone auto-configuration** (no device hunting)
- **Wake word support** (pre-recording buffer)
- **Real-time processing** (no file I/O delays)

For legacy applications that don't need real-time performance, the original MicManager remains available and supported.