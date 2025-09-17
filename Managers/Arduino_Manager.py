"""
Arduino_Manager.py
Unified Arduino device manager for Jetson Hardware

Manages all Arduino-connected devices with thread-safe resource management
following the established pattern of other hardware managers.

Supports:
- DC Motor control (left/right drive motors)
- Future expansion: Servos, additional LEDs, sensors
- Device lifecycle management
- Emergency stop functionality
- Configuration-based device setup
"""

import threading
import logging
import os
import signal
import time
import fcntl
from typing import Dict, Optional, Any, List
import json

from Libs.ArduinoLib import ArduinoConnection, ArduinoProtocol
from Libs.Arduino.MotorDevice import DCMotor, DifferentialDrive

class ArduinoManager:
    """
    Thread-safe manager for all Arduino devices
    
    Follows the same pattern as MicManager and LEDManager:
    - File locking for exclusive access
    - Resource acquisition/release
    - Background operation support
    - Comprehensive logging
    """
    
    _lock = threading.Lock()
    _file_lock_path = '/tmp/arduino_manager.lock'
    _file_lock = None
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200, 
                 log_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize Arduino Manager
        
        Args:
            port: Arduino serial port
            baudrate: Serial communication speed
            log_path: Path to log file
            config_path: Path to device configuration file
        """
        # Connection setup
        self.port = port
        self.baudrate = baudrate
        self.arduino = ArduinoConnection(port=port, baudrate=baudrate)
        
        # Manager state
        self._acquired = False
        self._initialized = False
        self._stop_requested = False
        
        # Device storage
        self._devices: Dict[str, Any] = {}
        self._motors: Dict[str, DCMotor] = {}
        
        # Differential drive support
        self._diff_drive: Optional[DifferentialDrive] = None
        
        # Setup logging
        log_path = log_path or os.environ.get('ARDUINO_LOG_PATH', 
                                            os.path.join(os.getcwd(), "Managers/logs/arduino_manager.log"))
        self._setup_logging(log_path)
        
        # Load configuration
        self.config_path = config_path or os.path.join(os.getcwd(), "config/arduino_config.json")
        self._load_configuration()
        
    def _setup_logging(self, log_path: str):
        """Setup logging configuration"""
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_configuration(self):
        """Load device configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                # Create default configuration
                self.config = self._create_default_config()
                self._save_configuration()
                self.logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default Arduino configuration"""
        return {
            "connection": {
                "port": "/dev/ttyUSB0",
                "baudrate": 115200,
                "timeout": 1.0
            },
            "motors": {
                "left_motor": {
                    "motor_id": 0,
                    "pwm_pin": 5,
                    "direction_pin": 7,
                    "max_speed": 100,
                    "acceleration_limit": 50
                },
                "right_motor": {
                    "motor_id": 1,
                    "pwm_pin": 6,
                    "direction_pin": 8,
                    "max_speed": 100,
                    "acceleration_limit": 50
                }
            },
            "differential_drive": {
                "enabled": True,
                "wheelbase": 1.0
            }
        }
    
    def _save_configuration(self):
        """Save current configuration to file"""
        try:
            config_dir = os.path.dirname(self.config_path)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.debug(f"Saved configuration to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def acquire(self) -> bool:
        """
        Acquire exclusive access to Arduino hardware
        
        Returns:
            bool: True if acquired successfully
        """
        try:
            ArduinoManager._lock.acquire()
            self._file_lock = open(self._file_lock_path, 'w')
            fcntl.flock(self._file_lock, fcntl.LOCK_EX)
            self._acquired = True
            
            # Connect to Arduino
            if not self.arduino.connect():
                self.release()
                return False
                
            # Initialize devices
            if not self._initialize_devices():
                self.release()
                return False
                
            self._initialized = True
            self.logger.info("Arduino Manager acquired and initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acquire Arduino Manager: {e}")
            self.release()
            return False
    
    def release(self):
        """Release Arduino hardware access"""
        try:
            self._stop_requested = True
            
            # Shutdown all devices
            self._shutdown_devices()
            
            # Disconnect Arduino
            if self.arduino.is_connected():
                self.arduino.disconnect()
            
            # Release file lock
            self._acquired = False
            self._initialized = False
            
            if self._file_lock:
                fcntl.flock(self._file_lock, fcntl.LOCK_UN)
                self._file_lock.close()
                self._file_lock = None
                
            ArduinoManager._lock.release()
            self.logger.info("Arduino Manager released")
            
        except Exception as e:
            self.logger.error(f"Error during Arduino Manager release: {e}")
    
    def _initialize_devices(self) -> bool:
        """Initialize all configured devices"""
        try:
            # Initialize motors
            motor_config = self.config.get('motors', {})
            for motor_name, motor_settings in motor_config.items():
                motor = DCMotor(
                    device_id=motor_name,
                    arduino_connection=self.arduino,
                    motor_id=motor_settings['motor_id'],
                    pwm_pin=motor_settings['pwm_pin'],
                    direction_pin=motor_settings.get('direction_pin')
                )
                
                if motor.initialize():
                    motor.set_max_speed(motor_settings.get('max_speed', 100))
                    motor.set_acceleration_limit(motor_settings.get('acceleration_limit', 50))
                    self._motors[motor_name] = motor
                    self._devices[motor_name] = motor
                    self.logger.info(f"Initialized motor: {motor_name}")
                else:
                    self.logger.error(f"Failed to initialize motor: {motor_name}")
                    return False
            
            # Setup differential drive if enabled
            diff_config = self.config.get('differential_drive', {})
            if diff_config.get('enabled', False):
                if 'left_motor' in self._motors and 'right_motor' in self._motors:
                    self._diff_drive = DifferentialDrive(
                        left_motor=self._motors['left_motor'],
                        right_motor=self._motors['right_motor'],
                        wheelbase=diff_config.get('wheelbase', 1.0)
                    )
                    self.logger.info("Differential drive initialized")
                else:
                    self.logger.warning("Cannot initialize differential drive - missing motors")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Device initialization failed: {e}")
            return False
    
    def _shutdown_devices(self):
        """Shutdown all devices safely"""
        for device_name, device in self._devices.items():
            try:
                device.shutdown()
                self.logger.info(f"Shutdown device: {device_name}")
            except Exception as e:
                self.logger.error(f"Error shutting down {device_name}: {e}")
        
        self._devices.clear()
        self._motors.clear()
        self._diff_drive = None
    
    # Motor Control Methods
    def motor(self, motor_name: str) -> Optional[DCMotor]:
        """
        Get motor instance by name
        
        Args:
            motor_name: Motor identifier (e.g., 'left_motor', 'right_motor')
            
        Returns:
            DCMotor instance or None if not found
        """
        return self._motors.get(motor_name)
    
    def set_motor_speed(self, motor_name: str, speed: int, immediate: bool = False) -> bool:
        """
        Set individual motor speed
        
        Args:
            motor_name: Motor identifier
            speed: Speed percentage (-100 to 100)
            immediate: Skip acceleration limiting if True
            
        Returns:
            bool: True if successful
        """
        if not self._check_ready():
            return False
            
        motor = self._motors.get(motor_name)
        if motor is None:
            self.logger.error(f"Motor not found: {motor_name}")
            return False
            
        return motor.set_speed(speed, immediate)
    
    def stop_motor(self, motor_name: str) -> bool:
        """
        Stop individual motor
        
        Args:
            motor_name: Motor identifier
            
        Returns:
            bool: True if successful
        """
        if not self._check_ready():
            return False
            
        motor = self._motors.get(motor_name)
        if motor is None:
            self.logger.error(f"Motor not found: {motor_name}")
            return False
            
        return motor.stop()
    
    def stop_all_motors(self) -> bool:
        """
        Stop all motors
        
        Returns:
            bool: True if all motors stopped successfully
        """
        if not self._check_ready():
            return False
            
        success = True
        for motor_name, motor in self._motors.items():
            if not motor.stop():
                success = False
                self.logger.error(f"Failed to stop motor: {motor_name}")
        
        return success
    
    # Differential Drive Methods
    def drive(self, linear_speed: float, angular_speed: float) -> bool:
        """
        Drive using differential drive kinematics
        
        Args:
            linear_speed: Forward/backward speed (-100 to 100)
            angular_speed: Turning speed (-100 to 100, negative = left)
            
        Returns:
            bool: True if successful
        """
        if not self._check_ready():
            return False
            
        if self._diff_drive is None:
            self.logger.error("Differential drive not initialized")
            return False
            
        return self._diff_drive.drive(linear_speed, angular_speed)
    
    def drive_forward(self, speed: int = 50) -> bool:
        """Drive forward at specified speed"""
        return self.drive(speed, 0)
    
    def drive_backward(self, speed: int = 50) -> bool:
        """Drive backward at specified speed"""
        return self.drive(-speed, 0)
    
    def turn_left(self, speed: int = 30) -> bool:
        """Turn left at specified speed"""
        return self.drive(0, -speed)
    
    def turn_right(self, speed: int = 30) -> bool:
        """Turn right at specified speed"""
        return self.drive(0, speed)
    
    def stop_driving(self) -> bool:
        """Stop differential drive"""
        if self._diff_drive:
            return self._diff_drive.stop()
        return self.stop_all_motors()
    
    # Emergency and Safety Methods
    def emergency_stop(self) -> bool:
        """
        Emergency stop all devices
        
        Returns:
            bool: True if all devices emergency stopped
        """
        self.logger.warning("Emergency stop triggered!")
        
        # Send Arduino emergency stop
        self.arduino.emergency_stop()
        
        # Emergency stop all motors
        success = True
        for motor_name, motor in self._motors.items():
            if not motor.emergency_stop():
                success = False
                self.logger.error(f"Failed to emergency stop motor: {motor_name}")
        
        return success
    
    def reset_emergency_stop(self):
        """Reset emergency stop condition for all devices"""
        for motor in self._motors.values():
            motor.reset_emergency_stop()
        self.logger.info("Emergency stop reset for all devices")
    
    # Status and Utility Methods
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            dict: Status of all devices and manager
        """
        status = {
            'manager': {
                'acquired': self._acquired,
                'initialized': self._initialized,
                'arduino_connected': self.arduino.is_connected(),
                'port': self.port,
                'device_count': len(self._devices)
            },
            'devices': {}
        }
        
        for device_name, device in self._devices.items():
            status['devices'][device_name] = device.get_status()
        
        if self._diff_drive:
            status['differential_drive'] = {
                'enabled': True,
                'left_motor': self._motors.get('left_motor', {}).get_status() if 'left_motor' in self._motors else None,
                'right_motor': self._motors.get('right_motor', {}).get_status() if 'right_motor' in self._motors else None
            }
        
        return status
    
    def _check_ready(self) -> bool:
        """Check if manager is ready for operations"""
        if not self._acquired:
            self.logger.error("Arduino Manager not acquired")
            return False
        if not self._initialized:
            self.logger.error("Arduino Manager not initialized")
            return False
        if not self.arduino.is_connected():
            self.logger.error("Arduino not connected")
            return False
        return True
    
    def is_ready(self) -> bool:
        """Check if manager is ready for operations"""
        return self._check_ready()
    
    # Configuration Methods
    def reload_configuration(self) -> bool:
        """
        Reload configuration from file
        
        Returns:
            bool: True if successful
        """
        try:
            self._load_configuration()
            self.logger.info("Configuration reloaded")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return False