
# Jetson Orin Nano Hardware Management

This repository provides Python libraries and managers for controlling Jetson Orin Nano hardware components, including LED, OLED, microphone, and speaker modules.


## Structure

- **Managers/**: High-level hardware management modules
	- `LED_Manager.py`, `OLED_Manager.py`, `Mic_Manager.py`, `Speaker_Manager.py`
	- Provide exclusive, thread-safe access to hardware devices
	- Always use `acquire()` and `release()` for safe access
	- Designed for integration into multiple projects without conflicts

- **Libs/**: Low-level hardware interface libraries
	- `CubeNanoLib.py`, `OledLib.py`, `MicLib.py`, `SpeakerLib.py`
	- Directly interact with hardware (I2C, ALSA, etc.)
	- Should only be used via Managers to avoid resource conflicts

- **docs/**: Documentation and hardware references
	- `hardware_reference.pdf`, `README.md`, and migrated docs from CubeNano/MicSpeakers
- `setup.py`: Python package setup
- `.gitignore`: Standard Python ignores
- `README.md`: Project overview

## Usage & Best Practices

- **Import Managers** in your application for hardware access:
	```python
	from Managers.LED_Manager import LEDManager
	led = LEDManager()
	led.acquire()
	led.set_effect(effect=1, speed=2, color=6)
	led.release()
	```
- **Never call Libs directly** unless you know what you're doing; always use Managers for thread/process safety.
- **Do not modify method signatures** in Libs/Managers unless you update all dependent projects.
- **Keep API stable**: If you need to change a method, consider adding a new method instead of changing/removing existing ones.
- **Document any changes** to Libs/Managers in the README and code docstrings.

## License
MIT

## Getting Started

1. Clone the repository
2. Install dependencies (see `setup.py`)
3. Review documentation in `docs/`

## License

MIT
