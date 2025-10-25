
# Jetson Orin Nano Hardware Documentation

This folder contains documentation and hardware references for Jetson Orin Nano hardware management, including migrated resources from CubeNano and MicSpeakers projects, plus Arduino motor control documentation.

## Included Documents

### Jetson Hardware Documentation
- `hardware_reference.pdf`: Jetson Orin Nano hardware reference (replace with actual PDF if available)
- `Wiring Instructions.pdf`: Wiring and connection guide (from CubeNano)
- `1. Install CubeNano driver library.pdf`: Driver installation instructions (from CubeNano)
- `2. OLED display.pdf`: OLED display usage and setup (from CubeNano)
- `4. RGB Light Bar Driver.pdf`: RGB LED bar driver documentation (from CubeNano)
- `6.I2C Communication Protocol.pdf`: I2C protocol details (from CubeNano)
- `MicSpeakers_README.md`: Microphone and speaker manager usage, API, and troubleshooting (from MicSpeakers)

### NEW: Streaming Audio Documentation
- **`Streaming_Mic_Manager_README.md`**: Complete guide for real-time voice control with StreamingMicManager
- **`Migration_Guide_MicManager.md`**: How to migrate from legacy MicManager to StreamingMicManager
- **`../config/usb_microphone_config.md`**: USB microphone hardware configuration and troubleshooting

### NEW: Robot Training Documentation
- **`TrainingDongle_README.md`**: Complete guide for 4-key USB training dongle system
- Robot feedback collection and LLM training data generation

### NEW: Display System Documentation  
- **`Display_Manager_README.md`**: Complete guide for framebuffer display management
- Hardware-accelerated graphics with threading and GStreamer integration

### Development Environment
- **`Development_Environment_Setup.md`**: 🛠️ Complete development environment setup
- VS Code configuration, Ruff linting, hardware-optimized coding standards

### Arduino Motor Control
- **Firmware**: `../Arduino/motor_controller/motor_controller.ino`
- **Hardware**: Arduino Nano with dual PWM ESC motor control
- **Communication**: 115200 baud serial over USB (/dev/ttyUSB0)
- **Features**: 
  - Dual motor control with PWM ESCs
  - Direction indicator LEDs
  - Watchdog timer (5 second timeout)
  - Emergency stop functionality
  - Serial command protocol
- **Testing**: `../SimpleTests/test_arduinoNano_motors.py`

## Usage
- Refer to each PDF for hardware setup, wiring, and driver installation.
- See `MicSpeakers_README.md` for microphone and speaker manager integration and best practices.

## Additional Resources
- [JetPack SDK Overview](https://docs.nvidia.com/jetson/jetpack/index.html)
- [Jetson Linux Developer Guide](https://docs.nvidia.com/jetson/archives/r38.2/DeveloperGuide/index.html)
- [Jetson Linux API Reference](https://docs.nvidia.com/jetson/archives/r38.2/ApiReference/index.html)
- [Jetson Platform Services (JPS)](https://docs.nvidia.com/jetson/jps/index.html)
- [NVIDIA Technical Blog](https://developer.nvidia.com/blog)

## License
MIT
