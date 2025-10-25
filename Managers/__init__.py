"""
Managers package - Hardware management modules for Jetson Orin Nano

This package contains all hardware management classes following the
jetson-hardware framework patterns with acquire/release semantics,
threading locks, and comprehensive error handling.
"""

# Import only available managers to avoid dependency issues
from .Display_Manager import DisplayManager

try:
    from .LED_Manager import LEDManager
except ImportError:
    LEDManager = None

try:
    from .OLED_Manager import OLEDManager
except ImportError:
    OLEDManager = None

try:
    from .Speaker_Manager import SpeakerManager
except ImportError:
    SpeakerManager = None

try:
    from .ArduinoMotor_Manager import ArduinoMotorManager
except ImportError:
    ArduinoMotorManager = None

try:
    from .LocalLLM_Manager import LocalLLMManager
except ImportError:
    LocalLLMManager = None

try:
    from .Mic_Manager import MicManager
except ImportError:
    MicManager = None

try:
    from .Mic_Manager_Streaming import StreamingMicManager
except ImportError:
    StreamingMicManager = None

try:
    from .TrainingDongle_Manager import TrainingDongleManager
except ImportError:
    TrainingDongleManager = None

try:
    from .Camera_Manager import CameraManager
except ImportError:
    CameraManager = None

__all__ = [
    'DisplayManager',
    'LEDManager', 
    'OLEDManager',
    'SpeakerManager',
    'ArduinoMotorManager',
    'LocalLLMManager',
    'MicManager',
    'StreamingMicManager',
    'TrainingDongleManager',
    'CameraManager'
]
