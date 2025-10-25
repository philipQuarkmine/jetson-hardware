"""
Arduino device package for Jetson Hardware

This package contains device-specific classes for Arduino-connected hardware:
- MotorDevice: DC brushed and brushless motors
- ServoDevice: Servo motor control
- LEDDevice: Additional LED control
- BaseDevice: Common device interface
"""

# Import main classes for easy access
try:
    from .BaseDevice import ArduinoDevice
    from .MotorDevice import DCMotor, DifferentialDrive
except ImportError as e:
    # Handle import errors gracefully during development
    pass
