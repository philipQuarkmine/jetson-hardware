
# Jetson Orin Nano Hardware Management

This repository provides Python libraries and managers for controlling Jetson Orin Nano hardware components, including LED, OLED, microphone, speaker modules, and Arduino-based motor control.


## Structure

- **Managers/**: High-level hardware management modules
	- `LED_Manager.py`, `OLED_Manager.py`, `Mic_Manager.py`, `Mic_Manager_Streaming.py`, `Speaker_Manager.py`, `TrainingDongle_Manager.py`
	- Provide exclusive, thread-safe access to hardware devices
	- Always use `acquire()` and `release()` for safe access
	- Designed for integration into multiple projects without conflicts
	- **NEW**: `Mic_Manager_Streaming.py` provides real-time voice activity detection and streaming audio
	- **NEW**: `TrainingDongle_Manager.py` provides 4-key USB feedback system for robot training

- **Libs/**: Low-level hardware interface libraries
	- `CubeNanoLib.py`, `OledLib.py`, `MicLib.py`, `SpeakerLib.py`, `TrainingDongleLib.py`
	- Directly interact with hardware (I2C, ALSA, USB HID, etc.)
	- Should only be used via Managers to avoid resource conflicts

- **Arduino/**: Arduino firmware for external hardware control
	- `motor_controller/`: Dual motor control via PWM ESCs
		- Arduino Nano firmware with serial communication
		- Watchdog timer and emergency stop functionality
		- PWM ESC control for left/right motors with direction indicators

- **docs/**: Documentation and hardware references
	- `hardware_reference.pdf`, `README.md`, and migrated docs from CubeNano/MicSpeakers
- **SimpleTests/**: Test scripts for individual hardware components
	- `test_led.py`, `test_mic.py`, `test_oled.py`, `test_speaker.py`, `test_training_dongle.py`
	- `test_arduinoNano_motors.py`: Comprehensive Arduino motor control testing
- `setup.py`: Python package setup
- `.gitignore`: Standard Python ignores
- `README.md`: Project overview

## Usage & Best Practices

### Jetson Hardware Managers
- **Import Managers** in your application for hardware access:
	```python
	from Managers.LED_Manager import LEDManager
	led = LEDManager()
	led.acquire()
	led.set_effect(effect=1, speed=2, color=6)
	led.release()
	```
- **For Real-time Voice Control** use the new Streaming Mic Manager:
	```python
	from Managers.Mic_Manager_Streaming import StreamingMicManager
	mic = StreamingMicManager()
	mic.acquire()
	
	# Set up voice activity detection callback
	def on_speech_detected(audio_data, sample_rate):
		print(f"Speech detected: {len(audio_data)} samples")
	
	mic.start_voice_detection(callback=on_speech_detected)
	# ... your voice processing logic ...
	mic.stop_voice_detection()
	mic.release()
	```
- **For Robot Training Feedback** use the Training Dongle Manager:
	```python
	from Managers.TrainingDongle_Manager import TrainingDongleManager
	trainer = TrainingDongleManager()
	trainer.acquire()
	
	# Set up feedback callback  
	def on_feedback(event):
		emojis = {1: "😍", 2: "😊", 3: "😬", 4: "💥"}
		print(f"Trainer feedback: {event.score.name} {emojis[event.score.value]} (Key {event.key_number})")
	
	trainer.start_feedback_monitoring(callback=on_feedback)
	# ... robot performs actions while trainer provides feedback ...
	trainer.stop_feedback_monitoring()
	trainer.release()
	```
- **Never call Libs directly** unless you know what you're doing; always use Managers for thread/process safety.

### Arduino Motor Control
- **Hardware**: Arduino Nano with dual PWM ESCs for motor control
- **Connection**: USB serial communication at 115200 baud
- **Safety**: Built-in watchdog timer and emergency stop functionality
- **Testing**: Use `SimpleTests/test_arduinoNano_motors.py` for comprehensive motor testing

#### Arduino Motor Commands
```python
import serial
arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# Test connection
arduino.write(b'PING\n')
response = arduino.readline().decode().strip()  # Should return "PONG"

# Control motors (speed: -100 to 100, duration in ms)
arduino.write(b'MOTOR_RIGHT:50:2000\n')  # Right motor 50% for 2 seconds
arduino.write(b'MOTOR_LEFT:-30:1500\n')  # Left motor reverse 30% for 1.5 seconds
arduino.write(b'MOTOR_BOTH:75:3000\n')  # Both motors 75% for 3 seconds
arduino.write(b'EMERGENCY_STOP\n')      # Immediate stop
```

### Development Guidelines
- **Do not modify method signatures** in Libs/Managers unless you update all dependent projects.
- **Keep API stable**: If you need to change a method, consider adding a new method instead of changing/removing existing ones.
- **Document any changes** to Libs/Managers in the README and code docstrings.

## License
MIT

## Getting Started

### Jetson Hardware Setup
1. Clone the repository
2. Install dependencies (see `setup.py`)
3. Review documentation in `docs/`

### Arduino Motor Control Setup
1. **Hardware Requirements**:
   - Arduino Nano (or compatible)
   - 2x PWM ESCs for motor control
   - USB cable for serial communication

2. **Arduino Setup**:
   ```bash
   # Install Arduino CLI (if not already installed)
   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
   
   # Install AVR core
   arduino-cli core install arduino:avr
   
   # Install Servo library
   arduino-cli lib install Servo
   
   # Compile and upload firmware
   cd Arduino/motor_controller
   arduino-cli compile --fqbn arduino:avr:nano motor_controller.ino
   arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano motor_controller.ino
   ```

3. **Test Motor Control**:
   ```bash
   cd SimpleTests
   python test_arduinoNano_motors.py
   ```

## License

MIT
