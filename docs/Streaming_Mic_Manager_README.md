# Streaming Mic Manager Documentation

## Overview

The `StreamingMicManager` is an enhanced microphone manager designed for real-time voice activity detection and streaming audio processing. It's optimized for voice command systems and robot control applications with sub-second latency requirements.

## Key Features

- **Real-time Voice Activity Detection (VAD)**: Automatically detects when someone starts and stops speaking
- **USB Microphone Auto-Detection**: Automatically finds and configures USB audio devices
- **Auto-calibrating Thresholds**: Adapts to environment noise levels
- **Pre-recording Buffer**: Captures speech beginning (like wake words) that occur before detection trigger
- **Thread-safe Operation**: Safe for use in multi-threaded applications
- **Hysteresis Thresholds**: Different start/continue levels prevent flickering detection

## Hardware Configuration

### Supported Audio Devices

The system automatically detects USB microphones and configures them properly:

- **Primary Target**: USB Audio Device (hw:0,0)
- **Sample Rate**: Auto-detected (typically 44100Hz for USB mics)
- **Format**: 16-bit PCM
- **Channels**: Mono (1 channel)

### Tested Hardware

- USB Audio Device (Generic USB microphones)
- Sample rates: 44100Hz (most common), 16000Hz, 48000Hz
- Works with standard USB microphones without additional drivers

## Quick Start

### Basic Usage

```python
from Managers.Mic_Manager_Streaming import StreamingMicManager

# Initialize and acquire exclusive access
mic = StreamingMicManager()
mic.acquire()

try:
    # Set up speech detection callback
    def handle_speech(audio_data, sample_rate):
        print(f"Speech detected: {len(audio_data)} samples at {sample_rate}Hz")
        # Process your audio here (send to STT, etc.)
    
    # Start voice activity detection
    mic.start_voice_detection(callback=handle_speech)
    
    # Your application runs here
    input("Press Enter to stop...")
    
finally:
    # Clean shutdown
    mic.stop_voice_detection()
    mic.release()
```

### Voice Command System

```python
from Managers.Mic_Manager_Streaming import StreamingMicManager

mic = StreamingMicManager()
mic.acquire()

# Configure for command detection (shorter timeouts)
def process_command(audio_data, sample_rate):
    """Process voice commands with fast response"""
    print(f"Command received: {len(audio_data)/sample_rate:.2f}s of audio")
    # Send to STT system for processing
    
try:
    mic.start_voice_detection(
        callback=process_command,
        min_speech_duration=0.3,     # Minimum 0.3s for commands
        max_silence_duration=1.0,    # 1.0s silence ends command
        max_recording_duration=8.0   # Max 8s per command
    )
    
    print("Voice command system ready...")
    print("Say: 'Hey robot, go forward' or 'Stop' or 'Turn left'")
    
    # Keep running
    while True:
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("Stopping voice command system...")
    
finally:
    mic.stop_voice_detection()
    mic.release()
```

## Configuration Parameters

### Voice Activity Detection

```python
mic.start_voice_detection(
    callback=your_function,           # Required: function to process detected speech
    
    # Timing controls
    min_speech_duration=0.5,          # Minimum speech length (seconds)
    max_silence_duration=2.0,         # Max silence before ending (seconds)  
    max_recording_duration=10.0,      # Max total recording length (seconds)
    
    # Pre-recording buffer (for wake words)
    pre_recording_duration=0.5,       # Capture 0.5s before speech detected
    
    # Advanced: Threshold controls (usually auto-calibrated)
    start_speech_threshold=None,      # None = auto-calibrate
    continue_speech_threshold=None    # None = auto-calibrate
)
```

### Auto-Calibration

The system automatically calibrates noise thresholds on startup:

1. **Background Noise Measurement**: 3 seconds of silence to establish baseline
2. **Threshold Calculation**: 
   - Start speech: `background_noise + (background_noise * 20 + 10)`
   - Continue speech: `start_threshold * 0.4` (hysteresis)
3. **Dynamic Range**: Handles 20-100 for normal speech, 100-500 for loud speech

## Integration with STT Systems

### With jetson-stt Streaming

```python
from Managers.Mic_Manager_Streaming import StreamingMicManager
import sys
sys.path.append('/home/phiip/jetson-stt')
from stt_streaming import StreamingJetsonSTT

# Initialize both systems
mic = StreamingMicManager()
stt = StreamingJetsonSTT()

mic.acquire()

def process_speech_to_text(audio_data, sample_rate):
    """Convert speech to text with <1s latency"""
    try:
        # Convert to format expected by STT
        transcript = stt.transcribe_audio_data(audio_data, sample_rate)
        print(f"📝 Transcript: '{transcript}'")
        
        # Process commands here
        if "stop" in transcript.lower():
            print("🛑 Emergency stop command!")
        elif "hey robot" in transcript.lower():
            print("🤖 Robot command detected!")
            
    except Exception as e:
        print(f"STT Error: {e}")

try:
    mic.start_voice_detection(
        callback=process_speech_to_text,
        min_speech_duration=0.3,     # Quick response
        max_silence_duration=1.0,    # Fast command cutoff
        pre_recording_duration=0.5   # Catch "Hey robot" wake words
    )
    
    print("Real-time voice control ready!")
    input("Press Enter to stop...")
    
finally:
    mic.stop_voice_detection()
    mic.release()
```

## Performance Characteristics

### Latency Measurements

- **Voice Detection**: <50ms from speech start to callback trigger
- **Audio Processing**: ~5-10ms per chunk (real-time)
- **Total STT Latency**: 300-800ms (when combined with jetson-stt)
- **Memory Usage**: ~50MB baseline, +10MB during active recording

### Optimization Settings

For best performance:

```python
# Robot/Command optimized settings
min_speech_duration=0.3      # Quick commands
max_silence_duration=1.0     # Fast cutoff
max_recording_duration=8.0   # Reasonable limit

# Conversation optimized settings  
min_speech_duration=0.5      # More complete phrases
max_silence_duration=2.0     # Natural pauses
max_recording_duration=30.0  # Longer responses
```

## Troubleshooting

### Common Issues

1. **No USB Microphone Detected**
   ```bash
   # Check available audio devices
   cat /proc/asound/cards
   arecord -l
   ```

2. **Audio Levels Too Low/High**
   ```bash
   # Test microphone levels
   arecord -D hw:0,0 -f S16_LE -r 44100 -c 1 -t wav /tmp/test.wav
   # Adjust system volume if needed
   alsamixer
   ```

3. **Threshold Calibration Issues**
   - Ensure quiet environment during startup calibration
   - Check system audio levels with `alsamixer`
   - Review calibration output in logs

### Debug Tools

Use the included test scripts:

```bash
# Test USB microphone detection and levels
cd /home/phiip/jetson-hardware
python debug_usb_mic.py

# Test complete voice detection system
cd /home/phiip/Agents/Zig_Zag  
python demo_realtime_stt.py
```

### Logging

Enable detailed logging:

```python
mic = StreamingMicManager(log_path="/path/to/debug.log")
# Check logs for detailed operation info
```

## Technical Details

### Voice Activity Detection Algorithm

1. **Continuous Audio Monitoring**: 1024-sample chunks at device sample rate
2. **Amplitude Calculation**: RMS amplitude with int16 → 0-1000 scaling
3. **Hysteresis Detection**: 
   - Speech starts when amplitude > `start_threshold`
   - Speech continues while amplitude > `continue_threshold` 
   - Speech ends after `max_silence_duration` below continue threshold
4. **Pre-recording Buffer**: Circular buffer captures audio before detection
5. **Output**: Complete audio segment including pre-buffer + detected speech

### Thread Safety

- **File Locking**: `/tmp/streaming_mic_manager.lock` prevents multiple instances
- **Thread Locks**: Internal threading.Lock() for thread safety
- **Clean Shutdown**: Proper resource cleanup on stop/release

### Memory Management

- **Circular Buffers**: Fixed-size deques prevent memory growth
- **Chunk Processing**: Small 1024-sample chunks for real-time processing  
- **Automatic Cleanup**: Audio data cleared after callback processing

## Future Enhancements

- **Multiple Wake Words**: Support for different wake word patterns
- **Noise Cancellation**: Advanced filtering for noisy environments
- **Speaker Separation**: Multi-person voice detection
- **Cloud Integration**: Optional cloud STT fallback
- **Configuration Profiles**: Pre-defined settings for different use cases

## License

MIT License - See main project LICENSE file.