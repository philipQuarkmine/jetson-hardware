#!/usr/bin/env python3
"""
Arduino Motor Manager for Jetson Hardware Platform

Provides thread-safe, real-time control of dual motors via Arduino Nano.
Supports both simple direct speed control (primary interface for LLM training)
and high-level movement helpers (for initial training and emergency situations).

Motor Configuration:
- Left Motor (ID 0): Left side of robot
- Right Motor (ID 1): Right side of robot
- Speed Range: -100% (full reverse) to +100% (full forward), 0% = stop

Movement Logic:
- Forward: Both motors positive speed
- Reverse: Both motors negative speed  
- Right turn: Left motor positive, right motor stopped/negative
- Left turn: Right motor positive, left motor stopped/negative

Hardware Requirements:
- Arduino Nano with motor_controller.ino firmware
- USB serial connection (typically /dev/ttyUSB0)
- Dual PWM ESCs connected to pins 5 (left) and 6 (right)

Usage:
    manager = ArduinoMotorManager()
    manager.acquire()
    
    # Primary interface for LLM training
    manager.set_motor_speeds(left=50, right=-30)  # Custom movement
    
    # High-level helpers for basic training
    manager.move_forward(speed=40)     # Both motors forward
    manager.turn_right(speed=30)       # Left motor forward, right stopped
    manager.emergency_stop()           # Immediate safety stop
    
    manager.release()
"""

import serial
import threading
import fcntl
import time
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MotorStatus(Enum):
    """Motor system status states."""
    READY = "ready"
    MOVING = "moving"
    EMERGENCY_STOP = "emergency_stop"
    ERROR = "error"
    DISCONNECTED = "disconnected"


@dataclass
class MotorState:
    """Current state of the motor system."""
    left_speed: int          # Current left motor speed (-100 to 100)
    right_speed: int         # Current right motor speed (-100 to 100)
    status: MotorStatus      # System status
    emergency_stop: bool     # Emergency stop active
    last_command_time: float # Timestamp of last command
    arduino_time: int        # Arduino uptime in milliseconds


class ArduinoMotorManager:
    """
    Thread-safe manager for Arduino-based dual motor control.
    
    Provides real-time communication with Arduino Nano running motor_controller.ino
    firmware. Supports both direct speed control for LLM training and high-level
    movement commands for initial training and emergency situations.
    """
    
    def __init__(self, port: str = "/dev/ttyUSB0", baud_rate: int = 115200):
        """
        Initialize Arduino Motor Manager.
        
        Args:
            port: Serial port for Arduino communication
            baud_rate: Communication speed (must match Arduino firmware)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.lock_file_path = "/tmp/arduino_motor_manager.lock"
        
        # Serial communication
        self.serial_connection: Optional[serial.Serial] = None
        self.communication_lock = threading.Lock()
        
        # Motor state tracking
        self.current_state = MotorState(
            left_speed=0,
            right_speed=0,
            status=MotorStatus.DISCONNECTED,
            emergency_stop=False,
            last_command_time=0.0,
            arduino_time=0
        )
        
        # Logging
        self.logger = logging.getLogger(f"ArduinoMotorManager_{id(self)}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Manager state
        self._acquired = False
        self._lock_file = None
        
        self.logger.info("ArduinoMotorManager initialized")

    def acquire(self) -> bool:
        """
        Acquire exclusive access to the Arduino motor system.
        
        Returns:
            True if successfully acquired, False if already in use
        """
        try:
            self._lock_file = open(self.lock_file_path, 'w')
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._acquired = True
            self.logger.info("ArduinoMotorManager acquired (file lock)")
            
            # Initialize Arduino connection
            if self._connect_arduino():
                return True
            else:
                self.release()
                return False
                
        except (IOError, OSError):
            self.logger.warning("ArduinoMotorManager already in use")
            if self._lock_file:
                self._lock_file.close()
                self._lock_file = None
            return False

    def release(self):
        """Release access to the Arduino motor system."""
        if self._acquired:
            # Emergency stop before releasing
            self.emergency_stop()
            
            # Close Arduino connection
            self._disconnect_arduino()
            
            # Release file lock
            if self._lock_file:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
                self._lock_file = None
            
            self._acquired = False
            self.logger.info("ArduinoMotorManager released")

    def _connect_arduino(self) -> bool:
        """
        Establish serial connection with Arduino.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=2.0
            )
            time.sleep(2.0)  # Arduino reset delay
            self.serial_connection.reset_input_buffer()
            
            # Test communication
            response = self._send_command("PING")
            if response == "PONG":
                self.logger.info(f"Arduino connected on {self.port}")
                
                # Reset to clean state
                self._send_command("RESET")
                self._update_status()
                
                self.current_state.status = MotorStatus.READY
                return True
            else:
                self.logger.error(f"Arduino not responding (got: {response})")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Arduino: {e}")
            self.current_state.status = MotorStatus.ERROR
            return False

    def _disconnect_arduino(self):
        """Close Arduino serial connection."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.logger.info("Arduino connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing Arduino connection: {e}")
        
        self.serial_connection = None
        self.current_state.status = MotorStatus.DISCONNECTED

    def _send_command(self, command: str) -> Optional[str]:
        """
        Send command to Arduino and get response.
        
        Args:
            command: Command string to send
            
        Returns:
            Response string or None if error
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            self.logger.error("Arduino not connected")
            return None
        
        with self.communication_lock:
            try:
                # Clear any pending input
                self.serial_connection.reset_input_buffer()
                
                # Send command
                self.serial_connection.write(f"{command}\n".encode())
                
                # Read response with timeout
                response = self.serial_connection.readline().decode().strip()
                self.current_state.last_command_time = time.time()
                
                return response
                
            except Exception as e:
                self.logger.error(f"Communication error: {e}")
                self.current_state.status = MotorStatus.ERROR
                return None

    def _update_status(self):
        """Update motor state from Arduino."""
        response = self._send_command("STATUS")
        if response:
            try:
                # Parse: "MOTORS:left,right ESTOP:0/1 TIME:millis"
                parts = response.split()
                
                if len(parts) >= 3:
                    # Parse motor speeds
                    motors_part = parts[0]  # "MOTORS:left,right"
                    if motors_part.startswith("MOTORS:"):
                        speeds = motors_part[7:].split(",")
                        self.current_state.left_speed = int(speeds[0])
                        self.current_state.right_speed = int(speeds[1])
                    
                    # Parse emergency stop
                    estop_part = parts[1]  # "ESTOP:0/1"
                    if estop_part.startswith("ESTOP:"):
                        self.current_state.emergency_stop = (estop_part[6:] == "1")
                    
                    # Parse Arduino time
                    time_part = parts[2]  # "TIME:millis"
                    if time_part.startswith("TIME:"):
                        self.current_state.arduino_time = int(time_part[5:])
                
            except Exception as e:
                self.logger.warning(f"Failed to parse status: {e}")

    # PRIMARY INTERFACE: Direct Speed Control (for LLM training)
    
    def set_motor_speeds(self, left: int, right: int) -> bool:
        """
        Set both motor speeds directly (primary interface for LLM).
        
        Args:
            left: Left motor speed (-100 to 100, 0 = stop)
            right: Right motor speed (-100 to 100, 0 = stop)
            
        Returns:
            True if commands sent successfully
        """
        if not self._acquired:
            self.logger.error("Manager not acquired")
            return False
        
        # Validate speed ranges
        left = max(-100, min(100, left))
        right = max(-100, min(100, right))
        
        # Send commands to Arduino
        left_response = self._send_command(f"MOTOR:0:{left}")
        right_response = self._send_command(f"MOTOR:1:{right}")
        
        success = (left_response == "OK" and right_response == "OK")
        
        if success:
            self.current_state.left_speed = left
            self.current_state.right_speed = right
            self.current_state.status = MotorStatus.MOVING if (left != 0 or right != 0) else MotorStatus.READY
            self.logger.info(f"Motor speeds set: left={left}%, right={right}%")
        else:
            self.logger.error(f"Failed to set motor speeds: left={left_response}, right={right_response}")
        
        return success

    # HIGH-LEVEL HELPERS: Basic movements (for initial training)
    
    def move_forward(self, speed: int = 15) -> bool:
        """
        Move robot forward (both motors positive speed).
        
        Args:
            speed: Forward speed (1 to 100)
            
        Returns:
            True if successful
        """
        speed = max(1, min(100, abs(speed)))
        return self.set_motor_speeds(left=speed, right=speed)

    def move_reverse(self, speed: int = 15) -> bool:
        """
        Move robot in reverse (both motors negative speed).
        
        Args:
            speed: Reverse speed (1 to 100)
            
        Returns:
            True if successful
        """
        speed = max(1, min(100, abs(speed)))
        return self.set_motor_speeds(left=-speed, right=-speed)

    def turn_right(self, speed: int = 15) -> bool:
        """
        Turn robot right (left motor forward, right motor stopped).
        
        Args:
            speed: Turn speed (1 to 100)
            
        Returns:
            True if successful
        """
        speed = max(1, min(100, abs(speed)))
        return self.set_motor_speeds(left=speed, right=0)

    def turn_left(self, speed: int = 15) -> bool:
        """
        Turn robot left (right motor forward, left motor stopped).
        
        Args:
            speed: Turn speed (1 to 100)
            
        Returns:
            True if successful
        """
        speed = max(1, min(100, abs(speed)))
        return self.set_motor_speeds(left=0, right=speed)

    def stop(self) -> bool:
        """
        Stop both motors gently.
        
        Returns:
            True if successful
        """
        return self.set_motor_speeds(left=0, right=0)

    # EMERGENCY & SAFETY
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop - immediately halt all motors and lock system.
        
        Returns:
            True if emergency stop activated
        """
        if not self.serial_connection:
            return False
        
        response = self._send_command("ESTOP")
        success = (response == "OK")
        
        if success:
            self.current_state.left_speed = 0
            self.current_state.right_speed = 0
            self.current_state.emergency_stop = True
            self.current_state.status = MotorStatus.EMERGENCY_STOP
            self.logger.warning("Emergency stop activated")
        
        return success

    def reset_emergency_stop(self) -> bool:
        """
        Reset emergency stop state and return to normal operation.
        
        Returns:
            True if reset successful
        """
        response = self._send_command("RESET")
        success = (response == "OK")
        
        if success:
            self.current_state.emergency_stop = False
            self.current_state.status = MotorStatus.READY
            self.logger.info("Emergency stop reset")
        
        return success

    # STATUS & MONITORING
    
    def get_motor_state(self) -> MotorState:
        """
        Get current motor system state.
        
        Returns:
            Current MotorState with speeds, status, and timing info
        """
        self._update_status()
        return self.current_state

    def is_moving(self) -> bool:
        """Check if either motor is currently moving."""
        return self.current_state.left_speed != 0 or self.current_state.right_speed != 0

    def get_speeds(self) -> Tuple[int, int]:
        """
        Get current motor speeds.
        
        Returns:
            Tuple of (left_speed, right_speed)
        """
        return (self.current_state.left_speed, self.current_state.right_speed)

    def ping(self) -> bool:
        """
        Test Arduino communication.
        
        Returns:
            True if Arduino responds correctly
        """
        response = self._send_command("PING")
        return response == "PONG"

    # CONTEXT MANAGERS
    
    def __enter__(self):
        """Context manager entry."""
        if self.acquire():
            return self
        else:
            raise RuntimeError("Failed to acquire ArduinoMotorManager")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()