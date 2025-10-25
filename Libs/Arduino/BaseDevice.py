"""
BaseDevice.py
Base class for all Arduino-connected devices

Provides common interface for device management, pin tracking,
and communication with Arduino.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..ArduinoLib import ArduinoConnection

class ArduinoDevice(ABC):
    """
    Abstract base class for all Arduino devices
    
    Provides common functionality:
    - Pin usage tracking and documentation
    - Device lifecycle management
    - Error handling and logging
    - Safety features
    """
    
    def __init__(self, device_id: str, arduino_connection: 'ArduinoConnection'):
        """
        Initialize Arduino device
        
        Args:
            device_id: Unique identifier for this device
            arduino_connection: Shared Arduino connection
        """
        self.device_id = device_id
        self.arduino = arduino_connection
        self.logger = logging.getLogger(f"{__name__}.{device_id}")
        self._initialized = False
        self._pins_used: Dict[int, str] = {}
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the device
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    def shutdown(self):
        """
        Safely shutdown the device
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current device status
        
        Returns:
            dict: Status information
        """
        pass
    
    def _register_pin(self, pin: int, purpose: str):
        """
        Register pin usage for documentation
        
        Args:
            pin: Arduino pin number
            purpose: Description of pin usage
        """
        self._pins_used[pin] = purpose
        self.logger.debug(f"Registered pin {pin} for {purpose}")
    
    def get_pin_usage(self) -> Dict[int, str]:
        """
        Get pin usage documentation
        
        Returns:
            dict: Pin number -> purpose mapping
        """
        return self._pins_used.copy()
    
    def is_initialized(self) -> bool:
        """Check if device is initialized"""
        return self._initialized
    
    def _send_command(self, command: str) -> bool:
        """
        Send command to Arduino with device logging
        
        Args:
            command: Command string
            
        Returns:
            bool: True if command sent successfully
        """
        self.logger.debug(f"Sending command: {command}")
        success = self.arduino.send_command(command)
        if not success:
            self.logger.error(f"Failed to send command: {command}")
        return success
    
    def _send_command_and_wait(self, command: str, expected_response: str = "OK") -> bool:
        """
        Send command and wait for response with device logging
        
        Args:
            command: Command string
            expected_response: Expected response
            
        Returns:
            bool: True if expected response received
        """
        self.logger.debug(f"Sending command with response: {command}")
        success = self.arduino.send_command_and_wait(command, expected_response)
        if not success:
            self.logger.error(f"Command failed or unexpected response: {command}")
        return success
