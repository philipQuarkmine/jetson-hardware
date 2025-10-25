"""
ArduinoLib.py
Base Arduino communication library for Jetson Hardware

Handles serial communication with Arduino Nano for PWM motor control,
servo control, and additional hardware expansion.

Pin Usage Documentation:
========================
Arduino Nano Pins (for reference):
- Digital Pins: 2-13 (PWM capable: 3,5,6,9,10,11)
- Analog Pins: A0-A7
- Serial: Pins 0(RX), 1(TX) - USB communication to Jetson

Current Pin Assignments:
- Pin 5: Left Motor PWM (ESC signal)
- Pin 6: Right Motor PWM (ESC signal) 
- Pin 7: Left Motor Direction (if needed)
- Pin 8: Right Motor Direction (if needed)
- Pin 13: Built-in LED (status indicator)

Future Pin Reservations:
- Pin 9: Servo 1 (camera pan)
- Pin 10: Servo 2 (camera tilt)
- Pin 11: Additional PWM device
- Pins A0-A3: Sensor inputs (encoders, current sensing)
"""

import json
import logging
import threading
import time
from typing import Any, Dict, Optional

import serial


class ArduinoConnection:
    """
    Handles serial communication with Arduino Nano
    """
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize Arduino connection
        
        Args:
            port: Serial port (usually /dev/ttyUSB0 for Arduino Nano)
            baudrate: Communication speed (115200 recommended)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: serial.Serial | None = None
        self._lock = threading.Lock()
        self._connected = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        Establish connection to Arduino
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Wait for Arduino to reset and initialize
            time.sleep(2)
            
            # Test connection with ping
            if self._ping_arduino():
                self._connected = True
                self.logger.info(f"Arduino connected on {self.port}")
                return True
            else:
                self.logger.error("Arduino ping failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Arduino: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close connection to Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self._connected = False
            self.logger.info("Arduino disconnected")
    
    def is_connected(self) -> bool:
        """Check if Arduino is connected"""
        return self._connected and self.serial_conn and self.serial_conn.is_open
    
    def send_command(self, command: str) -> bool:
        """
        Send command to Arduino
        
        Args:
            command: Command string (will be terminated with \n)
            
        Returns:
            bool: True if command sent successfully
        """
        if not self.is_connected():
            self.logger.error("Arduino not connected")
            return False
            
        try:
            with self._lock:
                command_bytes = f"{command}\n".encode()
                self.serial_conn.write(command_bytes)
                self.serial_conn.flush()
                return True
        except Exception as e:
            self.logger.error(f"Failed to send command '{command}': {e}")
            return False
    
    def read_response(self, timeout: float | None = None) -> str | None:
        """
        Read response from Arduino
        
        Args:
            timeout: Override default timeout
            
        Returns:
            str: Response string or None if failed
        """
        if not self.is_connected():
            return None
            
        try:
            with self._lock:
                old_timeout = self.serial_conn.timeout
                if timeout is not None:
                    self.serial_conn.timeout = timeout
                    
                response = self.serial_conn.readline().decode('utf-8').strip()
                
                if timeout is not None:
                    self.serial_conn.timeout = old_timeout
                    
                return response if response else None
        except Exception as e:
            self.logger.error(f"Failed to read response: {e}")
            return None
    
    def send_command_and_wait(self, command: str, expected_response: str = "OK", timeout: float = 1.0) -> bool:
        """
        Send command and wait for expected response
        
        Args:
            command: Command to send
            expected_response: Expected response string
            timeout: Wait timeout
            
        Returns:
            bool: True if expected response received
        """
        if not self.send_command(command):
            return False
            
        response = self.read_response(timeout)
        if response == expected_response:
            return True
        else:
            self.logger.warning(f"Unexpected response to '{command}': got '{response}', expected '{expected_response}'")
            return False
    
    def _ping_arduino(self) -> bool:
        """
        Test Arduino connectivity with ping command
        
        Returns:
            bool: True if ping successful
        """
        return self.send_command_and_wait("PING", "PONG", timeout=2.0)
    
    def emergency_stop(self) -> bool:
        """
        Send emergency stop command to Arduino
        
        Returns:
            bool: True if stop command sent
        """
        self.logger.warning("Emergency stop triggered!")
        return self.send_command("ESTOP")


class ArduinoProtocol:
    """
    Defines the communication protocol with Arduino
    
    Command Format:
    ===============
    PING - Test connection (responds with PONG)
    ESTOP - Emergency stop all motors
    MOTOR:<id>:<speed> - Set motor speed (-100 to 100)
    SERVO:<id>:<angle> - Set servo angle (0 to 180)
    LED:<r>:<g>:<b> - Set status LED color
    STATUS - Get Arduino status
    """
    
    # Command prefixes
    PING = "PING"
    EMERGENCY_STOP = "ESTOP"
    MOTOR_CMD = "MOTOR"
    SERVO_CMD = "SERVO"
    LED_CMD = "LED"
    STATUS_CMD = "STATUS"
    
    # Motor IDs
    MOTOR_LEFT = 0
    MOTOR_RIGHT = 1
    
    # Standard responses
    RESPONSE_OK = "OK"
    RESPONSE_PONG = "PONG"
    RESPONSE_ERROR = "ERROR"
    
    @staticmethod
    def motor_command(motor_id: int, speed: int) -> str:
        """
        Create motor control command
        
        Args:
            motor_id: Motor ID (0=left, 1=right)
            speed: Speed percentage (-100 to 100)
            
        Returns:
            str: Formatted command
        """
        speed = max(-100, min(100, speed))  # Clamp to valid range
        return f"{ArduinoProtocol.MOTOR_CMD}:{motor_id}:{speed}"
    
    @staticmethod
    def servo_command(servo_id: int, angle: int) -> str:
        """
        Create servo control command
        
        Args:
            servo_id: Servo ID
            angle: Angle in degrees (0-180)
            
        Returns:
            str: Formatted command
        """
        angle = max(0, min(180, angle))  # Clamp to valid range
        return f"{ArduinoProtocol.SERVO_CMD}:{servo_id}:{angle}"
    
    @staticmethod
    def led_command(red: int, green: int, blue: int) -> str:
        """
        Create LED control command
        
        Args:
            red, green, blue: RGB values (0-255)
            
        Returns:
            str: Formatted command
        """
        r = max(0, min(255, red))
        g = max(0, min(255, green))
        b = max(0, min(255, blue))
        return f"{ArduinoProtocol.LED_CMD}:{r}:{g}:{b}"
