"""
TrainingDongleLib.py - Low-level library for 4-key USB training dongle

Hardware: RDing HK4-F1.3 Foot Switch (USB ID: 0c45:7403)
Purpose: Robot training feedback system with 4 programmable keys

This library provides direct access to the USB training dongle for capturing
key press events that will be used for LLM feedback and robot behavior scoring.

Key mappings:
- Key 1: Excellent (score: 1)
- Key 2: Good (score: 2) 
- Key 3: Poor (score: 3)
- Key 4: Failure (score: 4)

Features:
- Non-blocking key event detection
- Configurable key mappings
- Event timestamping for training data
- Thread-safe operation
- Auto-detection of training dongle device
"""

import os
import time
import threading
import select
import struct
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum


class TrainingScore(Enum):
    """Training feedback scores for robot actions (golf-style: lower is better)."""
    EXCELLENT = 1
    GOOD = 2  
    POOR = 3
    FAILURE = 4


@dataclass
class KeyEvent:
    """Represents a key press event from the training dongle."""
    key_number: int           # 1-4 for the four keys
    score: TrainingScore      # Mapped training score
    timestamp: float          # Unix timestamp
    event_type: str          # 'press' or 'release'
    raw_keycode: int         # Raw Linux keycode


class TrainingDongleLib:
    """Low-level library for USB training dongle interaction."""
    
    # Hardware identification
    VENDOR_ID = 0x0c45
    PRODUCT_ID = 0x7403
    DEVICE_NAME = "RDing HK4-F1.3"
    
    # Default key mappings (Linux keycodes to training keys)
    # Based on actual testing with RDing HK4-F1.3 device
    DEFAULT_KEY_MAPPING = {
        30: 1,   # KEY_A -> Key 1 (Excellent)
        48: 2,   # KEY_B -> Key 2 (Good)
        46: 3,   # KEY_C -> Key 3 (Poor)
        32: 4,   # KEY_D -> Key 4 (Failure)
    }
    
    def __init__(self, device_path: Optional[str] = None, 
                 key_mapping: Optional[Dict[int, int]] = None,
                 enable_logging: bool = True):
        """
        Initialize training dongle library.
        
        Args:
            device_path: Path to input device (auto-detected if None)
            key_mapping: Custom keycode to key number mapping
            enable_logging: Enable debug logging
        """
        self.device_path = device_path
        self.key_mapping = key_mapping or self.DEFAULT_KEY_MAPPING.copy()
        self.device_fd = None
        self.is_monitoring = False
        self.monitor_thread = None
        self.event_callback = None
        
        # Setup logging
        self.logger = logging.getLogger(f"TrainingDongle_{id(self)}")
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
        
        # Auto-detect device if not specified
        if not self.device_path:
            self.device_path = self._find_training_dongle()
            
        if self.device_path:
            self.logger.info(f"Training dongle found at: {self.device_path}")
        else:
            self.logger.warning("Training dongle not detected")
    
    def _find_training_dongle(self) -> Optional[str]:
        """Auto-detect the training dongle input device."""
        by_id_path = "/dev/input/by-id"
        
        if not os.path.exists(by_id_path):
            return None
            
        # Look for RDing device
        for device_file in os.listdir(by_id_path):
            if "RDing" in device_file and "HK4-F1.3" in device_file and "event-kbd" in device_file:
                device_path = os.path.join(by_id_path, device_file)
                self.logger.info(f"Found training dongle: {device_file}")
                return device_path
        
        # Fallback: check /proc/bus/input/devices
        try:
            with open("/proc/bus/input/devices", "r") as f:
                content = f.read()
                
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "RDing HK4-F1.3 Keyboard" in line:
                    # Look for the Handlers line 
                    for j in range(i, min(i + 10, len(lines))):
                        if lines[j].startswith("H: Handlers="):
                            handlers = lines[j].split("=")[1].strip()
                            for handler in handlers.split():
                                if handler.startswith("event"):
                                    device_path = f"/dev/input/{handler}"
                                    self.logger.info(f"Found training dongle via handlers: {device_path}")
                                    return device_path
        except Exception as e:
            self.logger.error(f"Error scanning for training dongle: {e}")
        
        return None
    
    def open_device(self) -> bool:
        """
        Open the training dongle device for reading.
        
        Returns:
            True if device opened successfully, False otherwise
        """
        if not self.device_path:
            self.logger.error("No device path available")
            return False
            
        try:
            self.device_fd = os.open(self.device_path, os.O_RDONLY | os.O_NONBLOCK)
            self.logger.info(f"Opened training dongle device: {self.device_path}")
            return True
        except PermissionError:
            self.logger.error(f"Permission denied accessing {self.device_path}. Try running with sudo or add user to input group.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to open device {self.device_path}: {e}")
            return False
    
    def close_device(self) -> None:
        """Close the training dongle device."""
        if self.device_fd is not None:
            try:
                os.close(self.device_fd)
                self.logger.info("Closed training dongle device")
            except Exception as e:
                self.logger.error(f"Error closing device: {e}")
            finally:
                self.device_fd = None
    
    def read_raw_event(self) -> Optional[tuple]:
        """
        Read a raw input event from the device.
        
        Returns:
            Tuple of (timestamp_sec, timestamp_usec, type, code, value) or None
        """
        if self.device_fd is None:
            return None
            
        try:
            # Use select to check if data is available
            ready, _, _ = select.select([self.device_fd], [], [], 0)
            if not ready:
                return None
                
            # Read input event (24 bytes on ARM64)
            data = os.read(self.device_fd, 24)
            if len(data) != 24:
                return None
                
            # Unpack input_event structure
            # struct input_event { timeval time; __u16 type; __u16 code; __s32 value; }
            event = struct.unpack('llHHi', data)
            return event
            
        except BlockingIOError:
            # No data available
            return None
        except Exception as e:
            self.logger.error(f"Error reading raw event: {e}")
            return None
    
    def parse_key_event(self, raw_event: tuple) -> Optional[KeyEvent]:
        """
        Parse a raw input event into a KeyEvent if it's a relevant key press.
        
        Args:
            raw_event: Raw input event tuple
            
        Returns:
            KeyEvent object or None if not a relevant key event
        """
        if not raw_event:
            return None
            
        timestamp_sec, timestamp_usec, event_type, keycode, value = raw_event
        
        # We only care about key events (type 1)
        if event_type != 1:
            return None
            
        # Check if this keycode is mapped to one of our training keys
        if keycode not in self.key_mapping:
            return None
            
        # Convert timestamp
        timestamp = timestamp_sec + (timestamp_usec / 1000000.0)
        
        # Determine event type
        if value == 1:
            event_type_str = "press"
        elif value == 0:
            event_type_str = "release"
        else:
            # Repeat events (value 2) - ignore for now
            return None
            
        # Map to training key
        key_number = self.key_mapping[keycode]
        score = TrainingScore(key_number)  # Golf-style: key 1=excellent, key 4=failure
        
        return KeyEvent(
            key_number=key_number,
            score=score,
            timestamp=timestamp,
            event_type=event_type_str,
            raw_keycode=keycode
        )
    
    def start_monitoring(self, callback: Callable[[KeyEvent], None]) -> bool:
        """
        Start monitoring for key events in a background thread.
        
        Args:
            callback: Function to call when a key event occurs
            
        Returns:
            True if monitoring started successfully
        """
        if self.is_monitoring:
            self.logger.warning("Already monitoring")
            return True
            
        if not self.open_device():
            return False
            
        self.event_callback = callback
        self.is_monitoring = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Started training dongle monitoring")
        return True
    
    def stop_monitoring(self) -> None:
        """Stop monitoring for key events."""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            
        self.close_device()
        self.logger.info("Stopped training dongle monitoring")
    
    def _monitor_loop(self) -> None:
        """Background thread loop for monitoring key events."""
        self.logger.info("Training dongle monitoring loop started")
        
        while self.is_monitoring:
            try:
                raw_event = self.read_raw_event()
                if raw_event:
                    key_event = self.parse_key_event(raw_event)
                    if key_event and self.event_callback:
                        self.event_callback(key_event)
                        
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Training dongle monitoring loop ended")
    
    def test_device(self, duration: float = 10.0) -> Dict[str, Any]:
        """
        Test the training dongle by monitoring for events for a specified duration.
        
        Args:
            duration: How long to monitor for events (seconds)
            
        Returns:
            Dictionary with test results
        """
        events = []
        
        def collect_event(event: KeyEvent):
            events.append(event)
            print(f"Key {event.key_number} {event.event_type} - Score: {event.score.name}")
        
        self.logger.info(f"Testing training dongle for {duration} seconds...")
        print(f"Press keys on the training dongle for {duration} seconds...")
        
        if not self.start_monitoring(collect_event):
            return {"success": False, "error": "Failed to start monitoring"}
        
        time.sleep(duration)
        self.stop_monitoring()
        
        # Analyze results
        key_presses = [e for e in events if e.event_type == "press"]
        key_counts = {}
        for event in key_presses:
            key_counts[event.key_number] = key_counts.get(event.key_number, 0) + 1
        
        return {
            "success": True,
            "duration": duration,
            "total_events": len(events),
            "key_presses": len(key_presses),
            "key_counts": key_counts,
            "events": events
        }
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get information about the training dongle device."""
        return {
            "vendor_id": hex(self.VENDOR_ID),
            "product_id": hex(self.PRODUCT_ID),
            "device_name": self.DEVICE_NAME,
            "device_path": self.device_path,
            "key_mapping": self.key_mapping,
            "is_connected": self.device_path is not None and os.path.exists(self.device_path or "")
        }
    
    def set_key_mapping(self, mapping: Dict[int, int]) -> None:
        """
        Update the keycode to training key mapping.
        
        Args:
            mapping: Dictionary of {keycode: key_number}
        """
        self.key_mapping = mapping.copy()
        self.logger.info(f"Updated key mapping: {self.key_mapping}")