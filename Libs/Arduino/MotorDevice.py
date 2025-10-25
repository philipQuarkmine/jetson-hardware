"""
MotorDevice.py
DC Motor control for Arduino-connected motors

Handles PWM motor control through ESCs connected to Arduino Nano.
Supports differential drive configuration with safety features.

Pin Assignments:
================
Left Motor (Motor ID 0):
- Pin 5: PWM signal to ESC
- Pin 7: Direction control (optional, if ESC supports it)

Right Motor (Motor ID 1): 
- Pin 6: PWM signal to ESC
- Pin 8: Direction control (optional, if ESC supports it)

ESC Configuration:
==================
- PWM frequency: 50Hz (20ms period)
- Pulse width: 1000-2000µs (1.0-2.0ms)
- 1500µs = neutral/stop
- 1000µs = full reverse
- 2000µs = full forward
"""

import time
from typing import Any, Dict, Optional

from ..ArduinoLib import ArduinoProtocol
from .BaseDevice import ArduinoDevice


class DCMotor(ArduinoDevice):
    """
    DC Motor control through Arduino PWM/ESC
    
    Supports bidirectional speed control with safety features:
    - Emergency stop capability
    - Speed ramping to prevent sudden acceleration
    - Motor state monitoring
    """
    
    # Motor IDs
    LEFT_MOTOR = ArduinoProtocol.MOTOR_LEFT
    RIGHT_MOTOR = ArduinoProtocol.MOTOR_RIGHT
    
    def __init__(self, device_id: str, arduino_connection, motor_id: int, 
                 pwm_pin: int, direction_pin: int | None = None):
        """
        Initialize DC Motor
        
        Args:
            device_id: Unique identifier (e.g., "left_motor", "right_motor")
            arduino_connection: Arduino connection instance
            motor_id: Motor ID (0=left, 1=right)
            pwm_pin: Arduino pin for PWM signal
            direction_pin: Arduino pin for direction (optional)
        """
        super().__init__(device_id, arduino_connection)
        
        self.motor_id = motor_id
        self.pwm_pin = pwm_pin
        self.direction_pin = direction_pin
        
        # Motor state
        self._current_speed = 0  # -100 to 100
        self._target_speed = 0
        self._max_speed = 100
        self._acceleration_limit = 50  # Max speed change per second
        self._last_update_time = time.time()
        
        # Safety features
        self._emergency_stopped = False
        self._enabled = True
        
        # Register pin usage for documentation
        self._register_pin(pwm_pin, f"Motor {motor_id} PWM/ESC signal")
        if direction_pin is not None:
            self._register_pin(direction_pin, f"Motor {motor_id} direction control")
    
    def initialize(self) -> bool:
        """
        Initialize motor - send initial stop command
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Send initial stop command
            success = self.stop()
            if success:
                self._initialized = True
                self.logger.info(f"Motor {self.device_id} initialized on pin {self.pwm_pin}")
            else:
                self.logger.error(f"Failed to initialize motor {self.device_id}")
            return success
        except Exception as e:
            self.logger.error(f"Motor initialization failed: {e}")
            return False
    
    def shutdown(self):
        """
        Safely shutdown motor
        """
        self.logger.info(f"Shutting down motor {self.device_id}")
        self.stop()
        self._initialized = False
    
    def set_speed(self, speed: int, immediate: bool = False) -> bool:
        """
        Set motor speed with optional ramping
        
        Args:
            speed: Speed percentage (-100 to 100)
                  Negative = reverse, Positive = forward, 0 = stop
            immediate: If True, skip acceleration limiting
            
        Returns:
            bool: True if command successful
        """
        if not self._initialized:
            self.logger.error("Motor not initialized")
            return False
            
        if self._emergency_stopped:
            self.logger.warning("Motor is emergency stopped")
            return False
            
        if not self._enabled:
            self.logger.warning("Motor is disabled")
            return False
        
        # Clamp speed to valid range
        speed = max(-self._max_speed, min(self._max_speed, speed))
        
        if immediate:
            return self._set_speed_immediate(speed)
        else:
            self._target_speed = speed
            return self._apply_acceleration_limiting()
    
    def _set_speed_immediate(self, speed: int) -> bool:
        """
        Set motor speed immediately without ramping
        
        Args:
            speed: Target speed (-100 to 100)
            
        Returns:
            bool: True if successful
        """
        command = ArduinoProtocol.motor_command(self.motor_id, speed)
        success = self._send_command_and_wait(command)
        
        if success:
            self._current_speed = speed
            self._target_speed = speed
            self._last_update_time = time.time()
            self.logger.debug(f"Motor {self.device_id} speed set to {speed}")
        
        return success
    
    def _apply_acceleration_limiting(self) -> bool:
        """
        Apply acceleration limiting to reach target speed gradually
        
        Returns:
            bool: True if successful
        """
        current_time = time.time()
        dt = current_time - self._last_update_time
        
        if dt <= 0:
            return True
            
        # Calculate maximum speed change allowed
        max_speed_change = self._acceleration_limit * dt
        speed_difference = self._target_speed - self._current_speed
        
        if abs(speed_difference) <= max_speed_change:
            # Can reach target speed
            new_speed = self._target_speed
        else:
            # Apply acceleration limiting
            if speed_difference > 0:
                new_speed = self._current_speed + max_speed_change
            else:
                new_speed = self._current_speed - max_speed_change
        
        return self._set_speed_immediate(int(new_speed))
    
    def stop(self) -> bool:
        """
        Stop motor immediately
        
        Returns:
            bool: True if successful
        """
        return self._set_speed_immediate(0)
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop - immediate stop and disable motor
        
        Returns:
            bool: True if successful
        """
        self.logger.warning(f"Emergency stop triggered for motor {self.device_id}")
        self._emergency_stopped = True
        return self.stop()
    
    def reset_emergency_stop(self):
        """
        Reset emergency stop condition
        """
        self.logger.info(f"Resetting emergency stop for motor {self.device_id}")
        self._emergency_stopped = False
    
    def set_max_speed(self, max_speed: int):
        """
        Set maximum speed limit
        
        Args:
            max_speed: Maximum speed percentage (0-100)
        """
        self._max_speed = max(0, min(100, max_speed))
        self.logger.info(f"Motor {self.device_id} max speed set to {self._max_speed}")
    
    def set_acceleration_limit(self, acceleration: int):
        """
        Set acceleration limiting
        
        Args:
            acceleration: Max speed change per second
        """
        self._acceleration_limit = max(1, acceleration)
        self.logger.info(f"Motor {self.device_id} acceleration limit set to {self._acceleration_limit}")
    
    def enable(self):
        """Enable motor"""
        self._enabled = True
        self.logger.info(f"Motor {self.device_id} enabled")
    
    def disable(self):
        """Disable motor"""
        self._enabled = False
        self.stop()
        self.logger.info(f"Motor {self.device_id} disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current motor status
        
        Returns:
            dict: Status information
        """
        return {
            'device_id': self.device_id,
            'motor_id': self.motor_id,
            'current_speed': self._current_speed,
            'target_speed': self._target_speed,
            'max_speed': self._max_speed,
            'acceleration_limit': self._acceleration_limit,
            'enabled': self._enabled,
            'emergency_stopped': self._emergency_stopped,
            'initialized': self._initialized,
            'pins': self.get_pin_usage()
        }
    
    def get_speed(self) -> int:
        """
        Get current motor speed
        
        Returns:
            int: Current speed (-100 to 100)
        """
        return self._current_speed


class DifferentialDrive:
    """
    Helper class for differential drive control
    
    Converts linear and angular velocity commands to left/right motor speeds
    """
    
    def __init__(self, left_motor: DCMotor, right_motor: DCMotor, wheelbase: float = 1.0):
        """
        Initialize differential drive
        
        Args:
            left_motor: Left motor instance
            right_motor: Right motor instance  
            wheelbase: Distance between wheels (for angular velocity calculation)
        """
        self.left_motor = left_motor
        self.right_motor = right_motor
        self.wheelbase = wheelbase
        
    def drive(self, linear_speed: float, angular_speed: float) -> bool:
        """
        Drive using linear and angular velocity
        
        Args:
            linear_speed: Forward/backward speed (-100 to 100)
            angular_speed: Turning speed (-100 to 100, negative = left)
            
        Returns:
            bool: True if both motors commanded successfully
        """
        # Convert to differential drive
        # Simple implementation - more sophisticated kinematics possible
        left_speed = linear_speed - angular_speed
        right_speed = linear_speed + angular_speed
        
        # Clamp to motor limits
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))
        
        # Command both motors
        left_success = self.left_motor.set_speed(int(left_speed))
        right_success = self.right_motor.set_speed(int(right_speed))
        
        return left_success and right_success
    
    def stop(self) -> bool:
        """
        Stop both motors
        
        Returns:
            bool: True if both motors stopped successfully
        """
        left_success = self.left_motor.stop()
        right_success = self.right_motor.stop()
        return left_success and right_success
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop both motors
        
        Returns:
            bool: True if both motors emergency stopped
        """
        left_success = self.left_motor.emergency_stop()
        right_success = self.right_motor.emergency_stop()
        return left_success and right_success
