
# Jetson Orin Nano Hardware & AI Management

This repository provides Python libraries and managers for controlling Jetson Orin Nano hardware components and local AI services, including LED, OLED, microphone, speaker modules, Arduino-based motor control, and local LLM management via Ollama.

## Quick Start

```python
# Hardware control
from Managers.LED_Manager import LEDManager
from Managers.ArduinoMotor_Manager import ArduinoMotorManager

# AI services
from Managers.LocalLLM_Manager import LocalLLMManager

# Hardware
led = LEDManager()
led.acquire()
led.set_effect(effect=1, speed=2, color=6)
led.release()

# Local AI
llm = LocalLLMManager()
llm.start_service()
response = llm.generate("Hello, how are you?", "llama3.2:3b")
print(response['text'])
llm.cleanup()
```

## Core Components

### 🤖 AI Services - LocalLLM_Manager
**Purpose**: Simple, focused manager for local LLM service with streaming support

```python
from Managers.LocalLLM_Manager import LocalLLMManager

# Basic usage
llm = LocalLLMManager()
llm.start_service()

# List available models
models = llm.list_models()
print(f"Available models: {models}")

# Generate response
result = llm.generate("What is the capital of France?", "llama3.2:3b")
if result['ok']:
    print(f"Response: {result['text']} (took {result['time_s']:.2f}s)")

# Streaming responses (real-time)
response = llm.generate_stream("Tell me a story", "llama3.2:3b")
for chunk in response.iter_lines():
    if chunk:
        data = json.loads(chunk.decode('utf-8'))
        if not data.get('done', False):
            print(data.get('response', ''), end='', flush=True)

# Performance optimization
llm.keep_model_warm("llama3.2:3b")  # Keep model loaded for instant responses
llm.clear_model_cache()              # Free GPU memory when needed

# Always cleanup
llm.cleanup()
```

**Key Features**:
- ✅ **Simple & Focused**: Single responsibility - manage Ollama service
- ✅ **Streaming Support**: Real-time word-by-word responses via `generate_stream()`
- ✅ **Performance Tools**: Model warming and cache management
- ✅ **GPU Optimized**: Configured for Jetson with `OLLAMA_FLASH_ATTENTION=1`
- ✅ **Non-Aggressive**: Respects existing ollama instances
- ✅ **Clean Architecture**: Provides tools, UI programs handle their own concerns

**Interactive Chat Example**:
```bash
cd /home/phiip/jetson-hardware
python3 SimpleTests/interactive_chat.py
```
Features real-time streaming, model switching, chat history, and responsive user experience.

### 🔧 Hardware Managers

#### LED & Display Control
```python
from Managers.LED_Manager import LEDManager
from Managers.OLED_Manager import OLEDManager

# LED control
led = LEDManager()
led.acquire()
led.set_effect(effect=1, speed=2, color=6)
led.release()

# OLED display
oled = OLEDManager()
oled.acquire()
oled.display_text("Hello World!")
oled.release()
```

#### Audio Processing
```python
from Managers.Mic_Manager_Streaming import StreamingMicManager
from Managers.Speaker_Manager import SpeakerManager

# Real-time voice detection
mic = StreamingMicManager()
mic.acquire()

def on_speech_detected(audio_data, sample_rate):
    print(f"Speech detected: {len(audio_data)} samples")

mic.start_voice_detection(callback=on_speech_detected)
# ... voice processing ...
mic.stop_voice_detection()
mic.release()
```

#### Robot Motor Control
```python
from Managers.ArduinoMotor_Manager import ArduinoMotorManager

motors = ArduinoMotorManager()
motors.acquire()

# Direct speed control (ideal for LLM training)
motors.set_motor_speeds(left=50, right=-30)

# High-level movement helpers
motors.move_forward(speed=40)
motors.turn_right(speed=30)
motors.emergency_stop()

motors.release()
```

#### Camera & Vision System
```python
from Managers.Camera_Manager import CameraManager
from Managers.Display_Manager import DisplayManager

# USB Camera capture
camera = CameraManager()
camera.acquire()
camera.open_camera(camera_id=0, width=640, height=480, fps=30)

# Take photos
camera.save_image("/tmp/robot_view.jpg")

# Real-time display integration
display = DisplayManager()
display.acquire()

frame = camera.capture_frame()
if frame is not None:
    # Convert and display on framebuffer
    from PIL import Image
    frame_rgb = frame[:, :, ::-1]  # BGR to RGB
    pil_image = Image.fromarray(frame_rgb)
    pil_image.save("/tmp/live_view.jpg")
    display.show_image("/tmp/live_view.jpg", (320, 200), update=True)

camera.release()
display.release()
```

#### 🌙 Ambient Display & Screensavers
**Purpose**: Peaceful visual animations for ambient lighting and display protection

```python
# Quick launcher with menu
python3 SimpleTests/screensaver_launcher.py

# Direct screensaver execution
from Managers.Display_Manager import DisplayManager

# Simple breathing colors (ultra-low power)
python3 SimpleTests/simple_screensaver.py

# Advanced wave animation (smooth flowing patterns)
python3 SimpleTests/jetson_screensaver.py
```

**Features:**
- 🌊 **Enhanced Wave Animation**: Dramatic flowing waves with trailing edge animation
- 💤 **Smooth Breathing Colors**: Fluid brightness transitions at 15 FPS for seamless breathing effect  
- ⚡ **Optimized Performance**: Wave mode ~12 FPS, Breathing mode ~15 FPS for smooth visuals
- 🎨 **Extended Color Palettes**: 7 distinct color themes (Ocean, Emerald, Sunset, Amber, Teal, Rose, Lavender)
- ✨ **Peaceful Sparkles**: Slow-drifting ambient sparkles with gentle movement
- 🎭 **Anti-Flicker Technology**: Trailing edge erasing for smooth, matrix-free animation
- ⌨️ **Graceful Exit**: Ctrl+C to stop with clean display restoration

**Screensaver Options:**
- **Simple Screensaver**: Perfect for overnight ambient lighting, smooth breathing transitions
- **Enhanced Wave Screensaver**: Dramatic 150px tall waves, 7 color palettes, slow peaceful movement
- **Interactive Launcher**: Menu-driven selection with descriptions and easy switching

**Recent Enhancements (Oct 2025):**
- ✅ **Taller Waves**: Increased amplitude to 150px for more dramatic visual impact
- ✅ **Slower Movement**: Reduced wave speed to 0.3 for meditative, relaxing flow
- ✅ **Smoother Breathing**: 15 FPS for fluid brightness transitions without stepping
- ✅ **Enhanced Colors**: 7 distinct palettes with 2+ minute cycles for visible transitions
- ✅ **Anti-Flicker**: Trailing edge animation eliminates matrix-like flickering
- ✅ **Peaceful Sparkles**: Ultra-slow moving ambient dots (0.2x speed) for gentle ambiance

#### Training Feedback System
```python
from Managers.TrainingDongle_Manager import TrainingDongleManager

trainer = TrainingDongleManager()
trainer.acquire()

def on_feedback(event):
    emojis = {1: "😍", 2: "😊", 3: "😬", 4: "💥"}
    print(f"Feedback: {event.score.name} {emojis[event.score.value]}")

trainer.start_feedback_monitoring(callback=on_feedback)
# ... robot performs actions while trainer provides feedback ...
trainer.stop_feedback_monitoring()
trainer.release()
```

## Architecture Philosophy

> **"Good programs do clear tasks very well"**

Each manager has a **single responsibility**:
- **LocalLLM_Manager**: Service management + streaming tools
- **Interactive_Chat**: UI concerns + user experience  
- **Hardware Managers**: Exclusive, thread-safe hardware access
- **Libraries**: Low-level hardware interfaces

## Project Structure

```
jetson-hardware/
├── .vscode/                    # 🛠️ VS Code configuration
│   └── settings.json          #    Ruff + hardware dev settings
├── Managers/                   # High-level managers  
│   ├── LocalLLM_Manager.py    # 🤖 Local AI service management
│   ├── LED_Manager.py         # LED control
│   ├── OLED_Manager.py        # Display management
│   ├── Display_Manager.py     # 📺 Framebuffer display system
│   ├── Camera_Manager.py      # 📷 USB camera control & capture
│   ├── Mic_Manager_Streaming.py # Real-time audio
│   ├── Speaker_Manager.py     # Audio output
│   ├── ArduinoMotor_Manager.py # Motor control
│   └── TrainingDongle_Manager.py # Feedback system
├── Libs/                      # Low-level hardware interfaces
│   ├── DisplayLib.py          # 📺 Direct framebuffer access
│   ├── CameraLib.py           # 📷 Camera interface & control
│   └── [Other hardware libs]  # Hardware-specific interfaces
├── SimpleTests/               # Test & example programs
│   ├── interactive_chat.py    # 🚀 Streaming chat interface
│   └── test_display_manager.py # Display system testing
├── Arduino/                   # Arduino firmware
├── docs/                      # Documentation
│   └── Development_Environment_Setup.md # 🛠️ Dev setup guide
├── pyproject.toml            # 🔧 Ruff linting configuration
├── pyrightconfig.json        # 🔧 Type checking configuration  
└── README.md                 # This file
```

## Integration Guide for Other Programs

### Using LocalLLM_Manager in Your Projects

The `LocalLLM_Manager` is designed to be imported and used by other programs:

```python
from Managers.LocalLLM_Manager import LocalLLMManager

# In your application
class MyAIApp:
    def __init__(self):
        self.llm = LocalLLMManager()
        
    def start(self):
        self.llm.start_service()
        
    def chat(self, message, model="llama3.2:3b"):
        return self.llm.generate(message, model)
        
    def stream_chat(self, message, model="llama3.2:3b"):
        # Returns raw requests.Response for streaming
        return self.llm.generate_stream(message, model)
        
    def cleanup(self):
        self.llm.cleanup()
```

### Best Practices

1. **Always call `cleanup()`** when your program exits
2. **Use `generate_stream()`** for real-time user interfaces
3. **Use `keep_model_warm()`** for responsive interactions
4. **Handle your own UI buffering** - manager provides raw streams
5. **Import the manager** - don't try to manage ollama yourself

### Hardware Integration

```python
# Thread-safe hardware access
manager.acquire()
try:
    # Your hardware operations
    manager.some_operation()
finally:
    manager.release()
```

## Installation & Setup

### Prerequisites
- Jetson Orin Nano with JetPack
- Python 3.8+
- Ollama (for AI features)

### Setup
```bash
# Clone repository
git clone <repo-url>
cd jetson-hardware

# Install dependencies
pip install -r requirements.txt

# For AI features, install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull an AI model
ollama pull llama3.2:3b
```

### Test Installation
```bash
# Test hardware (if connected)
python3 SimpleTests/test_led.py

# Test AI services
python3 SimpleTests/interactive_chat.py

# Test display & screensavers
python3 SimpleTests/screensaver_launcher.py
python3 SimpleTests/simple_screensaver.py
python3 SimpleTests/jetson_screensaver.py
```

## Development Environment

### VS Code Setup (Recommended)
This project is optimized for VS Code with **Ruff linter** for hardware/robotics development:

**Required Extensions:**
- ✅ **Ruff** (`charliermarsh.ruff`) - Primary linter and formatter
- ✅ **Python** (`ms-python.python`) - Core Python support
- ✅ **Python Debugger** (`ms-python.debugpy`) - Debugging
- ✅ **Python Environments** (`ms-python.vscode-pylance`) - Environment management

**Extensions to Uninstall** (to prevent conflicts):
- ❌ **Pylance** - Too strict for hardware code
- ❌ **Pylint** - Conflicts with Ruff configuration

**Auto-Configuration:**
The project includes pre-configured files:
- `.vscode/settings.json` - VS Code settings optimized for Jetson development
- `pyproject.toml` - Ruff configuration with hardware-friendly rules
- `pyrightconfig.json` - Type checking configuration

### Code Style & Standards

**Formatting:** Auto-formatted with Ruff (88-100 character lines)
**Import Organization:** Automatic import sorting on save
**Type Hints:** Optional (hardware code often requires dynamic typing)
**Error Handling:** Explicit try/except preferred over `contextlib.suppress`

```python
# ✅ Hardware-friendly patterns
try:
    hardware.some_operation()
except:  # Broad exception for hardware reliability
    pass

# ✅ Hardware register access
GPIO_BASE = 0x7E200000  # Direct hardware addresses OK
register_value = ctypes.c_uint32.from_address(GPIO_BASE + offset)
```

## Development Guidelines

- **Stable APIs**: Don't modify method signatures without updating all dependent projects
- **Single Responsibility**: Each manager does one thing well  
- **Thread Safety**: Always use `acquire()`/`release()` for hardware
- **Clean Architecture**: Separate concerns between service management and UI
- **Hardware-First**: Code style prioritizes hardware reliability over strict typing
- **Ruff Compliance**: All code auto-formatted and linted with robotics-optimized rules

## License

MIT License - See LICENSE file for details

---

**🚀 Ready to build intelligent hardware applications with streaming AI and responsive controls!**
