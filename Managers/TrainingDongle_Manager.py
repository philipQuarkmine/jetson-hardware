"""
TrainingDongle_Manager.py - Manager for 4-key USB training dongle

Hardware: RDing HK4-F1.3 Foot Switch (USB ID: 0c45:7403)
Purpose: Thread-safe management of robot training feedback system

This manager provides exclusive, thread-safe access to the USB training dongle
for capturing trainer feedback during robot operation. Follows the jetson-hardware
manager pattern with acquire/release semantics and file locking.

Usage:
    from Managers.TrainingDongle_Manager import TrainingDongleManager
    
    manager = TrainingDongleManager()
    manager.acquire()
    
    try:
        def on_feedback(event):
            print(f"Trainer feedback: Key {event.key_number} - {event.score.name}")
        
        manager.start_feedback_monitoring(callback=on_feedback)
        # ... robot operates and trainer provides feedback ...
        
    finally:
        manager.stop_feedback_monitoring()
        manager.release()

Integration with LLM training:
    - Captures timestamped feedback events
    - Maps key presses to training scores (1=Excellent, 4=Failure - golf style)
    - Provides feedback history for training data
    - Thread-safe for use in real-time robot systems
"""

import threading
import logging
import fcntl
import os
import time
import json
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime, timedelta
from collections import deque

from TrainingDongleLib import TrainingDongleLib, KeyEvent, TrainingScore


class TrainingDongleManager:
    """
    Thread-safe manager for USB training dongle.
    
    Provides exclusive access to the training dongle hardware following
    the jetson-hardware manager pattern with file locking and proper
    resource management.
    """
    
    _lock = threading.Lock()
    _file_lock_path = '/tmp/training_dongle_manager.lock'
    
    def __init__(self, base_dir: Optional[str] = None, log_path: Optional[str] = None,
                 feedback_history_size: int = 1000):
        """
        Initialize training dongle manager.
        
        Args:
            base_dir: Base directory for logs and data
            log_path: Path for log file
            feedback_history_size: Maximum number of feedback events to keep in memory
        """
        self.base_dir = base_dir or os.environ.get('TRAINING_DONGLE_BASE_DIR', os.getcwd())
        self.feedback_history_size = feedback_history_size
        
        # Setup logging
        log_path = log_path or os.path.join(self.base_dir, "logs", "training_dongle_manager.log")
        self._setup_logging(log_path)
        
        # Initialize training dongle library
        self._dongle = TrainingDongleLib(enable_logging=False)  # Manager handles logging
        
        # Manager state
        self._acquired = False
        self._file_lock = None
        self._monitoring = False
        self._feedback_callback = None
        
        # Feedback history and statistics
        self._feedback_history = deque(maxlen=feedback_history_size)
        self._session_start_time = None
        self._last_feedback_time = None
        
        self.logger.info("TrainingDongleManager initialized")
    
    def _setup_logging(self, log_path: str) -> None:
        """Setup logging for the manager."""
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        self.logger = logging.getLogger(f"TrainingDongleManager_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler(log_path)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def acquire(self) -> bool:
        """
        Acquire exclusive access to the training dongle.
        
        Returns:
            True if successfully acquired, False otherwise
        """
        try:
            TrainingDongleManager._lock.acquire()
            
            # File-based locking for cross-process safety
            self._file_lock = open(self._file_lock_path, 'w')
            fcntl.flock(self._file_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            self._acquired = True
            self._session_start_time = time.time()
            
            self.logger.info("TrainingDongleManager acquired (file lock)")
            return True
            
        except BlockingIOError:
            self.logger.error("Training dongle already in use by another process")
            TrainingDongleManager._lock.release()
            return False
        except Exception as e:
            self.logger.error(f"Failed to acquire training dongle: {e}")
            TrainingDongleManager._lock.release()
            return False
    
    def release(self) -> None:
        """Release exclusive access to the training dongle."""
        if not self._acquired:
            return
        
        try:
            # Stop any active monitoring
            self.stop_feedback_monitoring()
            
            # Release file lock
            if self._file_lock:
                fcntl.flock(self._file_lock, fcntl.LOCK_UN)
                self._file_lock.close()
                self._file_lock = None
            
            self._acquired = False
            
            # Save session summary
            if self._session_start_time:
                session_duration = time.time() - self._session_start_time
                session_stats = self.get_session_statistics()
                self.logger.info(f"Session ended - Duration: {session_duration:.1f}s, "
                               f"Feedback events: {session_stats['total_feedback']}")
            
            TrainingDongleManager._lock.release()
            self.logger.info("TrainingDongleManager released (file lock)")
            
        except Exception as e:
            self.logger.error(f"Error releasing training dongle: {e}")
    
    def start_feedback_monitoring(self, callback: Callable[[KeyEvent], None]) -> bool:
        """
        Start monitoring for trainer feedback events.
        
        Args:
            callback: Function to call when feedback is received
            
        Returns:
            True if monitoring started successfully
        """
        if not self._acquired:
            self.logger.error("Must acquire manager before starting monitoring")
            return False
        
        if self._monitoring:
            self.logger.warning("Already monitoring for feedback")
            return True
        
        # Wrap callback to include history tracking
        def wrapped_callback(event: KeyEvent):
            self._record_feedback_event(event)
            if callback:
                callback(event)
        
        if not self._dongle.start_monitoring(wrapped_callback):
            self.logger.error("Failed to start dongle monitoring")
            return False
        
        self._monitoring = True
        self._feedback_callback = callback
        
        self.logger.info("Started training feedback monitoring")
        return True
    
    def stop_feedback_monitoring(self) -> None:
        """Stop monitoring for trainer feedback events."""
        if not self._monitoring:
            return
        
        self._dongle.stop_monitoring()
        self._monitoring = False
        self._feedback_callback = None
        
        self.logger.info("Stopped training feedback monitoring")
    
    def _record_feedback_event(self, event: KeyEvent) -> None:
        """Record a feedback event in the history."""
        self._feedback_history.append(event)
        self._last_feedback_time = event.timestamp
        
        self.logger.info(f"Feedback: Key {event.key_number} ({event.score.name}) "
                        f"at {datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S')}")
    
    def get_recent_feedback(self, seconds: float = 30.0) -> List[KeyEvent]:
        """
        Get feedback events from the last N seconds.
        
        Args:
            seconds: Time window to look back
            
        Returns:
            List of KeyEvent objects
        """
        if not self._feedback_history:
            return []
        
        cutoff_time = time.time() - seconds
        return [event for event in self._feedback_history if event.timestamp >= cutoff_time]
    
    def get_feedback_for_timespan(self, start_time: float, end_time: float) -> List[KeyEvent]:
        """
        Get feedback events within a specific timespan.
        
        Args:
            start_time: Unix timestamp for start of timespan
            end_time: Unix timestamp for end of timespan
            
        Returns:
            List of KeyEvent objects
        """
        return [event for event in self._feedback_history 
                if start_time <= event.timestamp <= end_time]
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for the current session.
        
        Returns:
            Dictionary with session statistics
        """
        if not self._session_start_time:
            return {"session_active": False}
        
        session_duration = time.time() - self._session_start_time
        session_feedback = [event for event in self._feedback_history 
                           if event.timestamp >= self._session_start_time]
        
        # Count feedback by score
        score_counts = {score: 0 for score in TrainingScore}
        for event in session_feedback:
            if event.event_type == "press":  # Only count key presses
                score_counts[event.score] += 1
        
        # Calculate average score
        total_feedback = sum(score_counts.values())
        if total_feedback > 0:
            weighted_score = sum(score.value * count for score, count in score_counts.items())
            average_score = weighted_score / total_feedback
        else:
            average_score = 0.0
        
        return {
            "session_active": True,
            "session_duration": session_duration,
            "session_start": self._session_start_time,
            "last_feedback": self._last_feedback_time,
            "total_feedback": total_feedback,
            "score_counts": {score.name: count for score, count in score_counts.items()},
            "average_score": average_score,
            "feedback_rate": total_feedback / session_duration if session_duration > 0 else 0.0
        }
    
    def export_feedback_data(self, filepath: Optional[str] = None) -> str:
        """
        Export feedback history to JSON file for training data.
        
        Args:
            filepath: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.base_dir, "training_data", f"feedback_{timestamp}.json")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert feedback history to serializable format
        feedback_data = {
            "export_timestamp": time.time(),
            "session_statistics": self.get_session_statistics(),
            "device_info": self._dongle.get_device_info(),
            "feedback_events": [
                {
                    "key_number": event.key_number,
                    "score": event.score.value,
                    "score_name": event.score.name,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "raw_keycode": event.raw_keycode
                }
                for event in self._feedback_history
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        
        self.logger.info(f"Exported {len(self._feedback_history)} feedback events to {filepath}")
        return filepath
    
    def test_dongle(self, duration: float = 10.0) -> Dict[str, Any]:
        """
        Test the training dongle functionality.
        
        Args:
            duration: How long to test for
            
        Returns:
            Test results dictionary
        """
        if not self._acquired:
            return {"success": False, "error": "Manager not acquired"}
        
        self.logger.info(f"Testing training dongle for {duration} seconds")
        return self._dongle.test_device(duration)
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get training dongle device information."""
        device_info = self._dongle.get_device_info()
        device_info.update({
            "manager_acquired": self._acquired,
            "monitoring_active": self._monitoring,
            "feedback_history_size": len(self._feedback_history)
        })
        return device_info
    
    def is_monitoring(self) -> bool:
        """Check if feedback monitoring is active."""
        return self._monitoring
    
    def wait_for_feedback(self, timeout: float = 30.0) -> Optional[KeyEvent]:
        """
        Wait for the next feedback event.
        
        Args:
            timeout: Maximum time to wait (seconds)
            
        Returns:
            Next KeyEvent or None if timeout
        """
        if not self._monitoring:
            self.logger.error("Not monitoring - start monitoring first")
            return None
        
        start_time = time.time()
        initial_count = len(self._feedback_history)
        
        while (time.time() - start_time) < timeout:
                if len(self._feedback_history) > initial_count:
                    # Only return the first new KeyEvent with event_type == 'press'
                    for event in list(self._feedback_history)[initial_count:]:
                        if hasattr(event, 'event_type') and event.event_type == 'press':
                            return event
                    # If no 'press' event found, keep waiting
                time.sleep(0.1)
        
        return None
    
    def get_feedback_summary(self, timespan_minutes: float = 5.0) -> Dict[str, Any]:
        """
        Get a summary of recent feedback for quick analysis.
        
        Args:
            timespan_minutes: Minutes to look back
            
        Returns:
            Summary dictionary
        """
        recent_events = self.get_recent_feedback(timespan_minutes * 60)
        key_presses = [e for e in recent_events if e.event_type == "press"]
        
        if not key_presses:
            return {
                "timespan_minutes": timespan_minutes,
                "total_feedback": 0,
                "average_score": 0.0,
                "score_distribution": {}
            }
        
        # Calculate statistics
        total_score = sum(event.score.value for event in key_presses)
        average_score = total_score / len(key_presses)
        
        score_counts = {}
        for event in key_presses:
            score_name = event.score.name
            score_counts[score_name] = score_counts.get(score_name, 0) + 1
        
        return {
            "timespan_minutes": timespan_minutes,
            "total_feedback": len(key_presses),
            "average_score": average_score,
            "score_distribution": score_counts,
            "feedback_rate_per_minute": len(key_presses) / timespan_minutes
        }