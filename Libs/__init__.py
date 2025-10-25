"""
Libs package - Hardware abstraction libraries for Jetson Orin Nano

This package contains low-level hardware abstraction libraries that provide
direct hardware access and optimized operations for various components.
"""

from .DisplayLib import DisplayLib
# Import only available modules to avoid dependency issues
try:
    from .ArduinoLib import ArduinoLib
except ImportError:
    ArduinoLib = None

try:  
    from .CubeNanoLib import CubeNano
except ImportError:
    CubeNano = None

try:
    from .MicLib import MicLib
except ImportError:
    MicLib = None

try:
    from .OledLib import OledLib
except ImportError:
    OledLib = None

try:
    from .SpeakerLib import SpeakerLib
except ImportError:
    SpeakerLib = None

try:
    from .TrainingDongleLib import TrainingDongleLib
except ImportError:
    TrainingDongleLib = None

__all__ = [
    'DisplayLib',
    'ArduinoLib',
    'CubeNano',
    'MicLib', 
    'OledLib',
    'SpeakerLib',
    'TrainingDongleLib'
]