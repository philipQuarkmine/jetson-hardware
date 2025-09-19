"""
Enhanced Mic Manager for Jetson Orin Nano with Real-time Streaming STT
Supports voice activity detection, auto-calibrating thresholds, and streaming audio processing.
"""

import threading
import logging
import signal
import sys
import os
import time
import fcntl
import queue
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from collections import deque

try:
    import sounddevice as sd
except ImportError:
    sd = None
    print("WARNING: sounddevice not installed. Install with: pip install sounddevice")

from MicLib import MicLib


class StreamingMicManager:
    """Enhanced MicManager with real-time voice activity detection and streaming capabilities."""
    
    _lock = threading.Lock()
    _file_lock_path = '/tmp/streaming_mic_manager.lock'
    _file_lock = None
    
    def __init__(self, base_dir=None, audio_device=None, log_path=None, 
                 sample_rate=None, chunk_size=1024, channels=1):
        """
        Initialize streaming mic manager.
        
        Args:
            base_dir: Base directory for recordings
            audio_device: Audio input device (None = auto-detect USB mic)
            log_path: Path for log files
            sample_rate: Audio sample rate (None = auto-detect from device)
            chunk_size: Audio buffer chunk size (smaller = lower latency)
            channels: Number of audio channels (1 for mono)
        """
        self.base_dir = base_dir or os.environ.get('MIC_BASE_DIR', os.getcwd())
        
        # Auto-detect USB microphone if not specified
        if audio_device is None:
            self.audio_device, self.sample_rate = self._find_usb_microphone()
        else:
            self.audio_device = audio_device
            self.sample_rate = sample_rate or 44100
        
        # If still no device found, use default
        if self.audio_device is None:
            self.audio_device = 0  # Default to first device
            self.sample_rate = 44100
        
        # Override sample rate if provided
        if sample_rate is not None:
            self.sample_rate = sample_rate
            
        self.chunk_size = chunk_size
        self.channels = channels
        
        # Voice Activity Detection parameters
        self.vad_threshold = 50.0  # Dynamic threshold, will auto-calibrate
        self.min_speech_duration = 0.3  # Minimum seconds of speech to trigger
        self.max_silence_duration = 1.0  # Seconds of silence to end recording (short for commands)
        self.max_recording_duration = 8.0  # Maximum recording length (prevent long captures)
        self.calibration_duration = 3.0  # Seconds to calibrate noise floor
        self.noise_floor = 10.0  # Baseline noise level
        
        # Pre-recording buffer to capture speech start
        self.pre_recording_duration = 0.5  # Seconds of audio to keep before speech detection
        self.pre_recording_buffer = deque(maxlen=int(self.pre_recording_duration * self.sample_rate / self.chunk_size))
        
        # Streaming state
        self._streaming = False
        self._stop_requested = False
        self._acquired = False
        self._audio_queue = queue.Queue()
        self._stream_thread = None
        self._processing_thread = None
        
        # Auto-calibration tracking
        self._amplitude_history = deque(maxlen=100)  # Keep last 100 amplitude readings
        self._last_calibration = None
        self._calibration_interval = timedelta(minutes=5)  # Re-calibrate every 5 minutes
        
        # Callbacks for real-time processing
        self.on_speech_start = None  # Called when speech detected
        self.on_speech_end = None    # Called when speech ends
        self.on_audio_chunk = None   # Called for each audio chunk
        self.on_amplitude_update = None  # Called with current amplitude level
        
        # Legacy MicLib for file recording compatibility
        self._mic = MicLib(base_dir=self.base_dir, audio_device=self.audio_device)
        
        self._setup_logging(log_path)
    
    def set_pre_recording_duration(self, duration_seconds: float):
        """
        Set the pre-recording buffer duration and rebuild the buffer.
        This ensures proper encapsulation of buffer management.
        
        Args:
            duration_seconds: Duration in seconds to buffer before speech detection
        """
        self.pre_recording_duration = max(0.1, min(duration_seconds, 5.0))  # Clamp between 0.1s and 5s
        
        # Rebuild buffer with new size
        new_buffer_size = int(self.pre_recording_duration * self.sample_rate / self.chunk_size)
        self.pre_recording_buffer = deque(maxlen=new_buffer_size)
        
        self.logger.info(f"Pre-recording buffer updated: {self.pre_recording_duration}s ({new_buffer_size} chunks)")
    
    def get_buffer_info(self) -> dict:
        """
        Get current buffer configuration information.
        
        Returns:
            dict: Buffer configuration details
        """
        buffer_size = len(self.pre_recording_buffer) if hasattr(self.pre_recording_buffer, '__len__') else self.pre_recording_buffer.maxlen
        chunks_per_second = self.sample_rate / self.chunk_size
        actual_duration = buffer_size / chunks_per_second if buffer_size else 0
        
        return {
            "duration_seconds": self.pre_recording_duration,
            "buffer_size_chunks": self.pre_recording_buffer.maxlen if self.pre_recording_buffer else 0,
            "current_chunks": len(self.pre_recording_buffer) if self.pre_recording_buffer else 0,
            "actual_duration_seconds": actual_duration,
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size,
            "chunks_per_second": chunks_per_second,
            "memory_usage_bytes": (self.pre_recording_buffer.maxlen * self.chunk_size * 4) if self.pre_recording_buffer else 0  # float32 = 4 bytes
        }
        
        if sd is None:
            logging.error("sounddevice not available - streaming features disabled")
            raise RuntimeError("sounddevice required for streaming functionality")
    
    def _find_usb_microphone(self):
        """
        Auto-detect USB microphone and its optimal sample rate.
        
        Returns:
            Tuple of (device_id, sample_rate) or (None, None) if not found
        """
        if sd is None:
            return None, None
        
        try:
            devices = sd.query_devices()
            
            # Look for USB Audio Device first (card 0)
            for i, device in enumerate(devices):
                if (device['max_input_channels'] > 0 and 
                    'USB Audio Device' in device['name']):
                    
                    # Test sample rates in order of preference
                    test_rates = [44100, 48000, 16000, 22050]
                    
                    for rate in test_rates:
                        try:
                            # Quick test to see if this rate works
                            test_audio = sd.rec(
                                int(0.01 * rate),  # 10ms test
                                samplerate=rate, 
                                channels=1, 
                                device=i, 
                                dtype='float32'
                            )
                            sd.wait()
                            
                            print(f"[USB MIC] Found device {i}: {device['name']} at {rate}Hz")
                            return i, rate
                            
                        except Exception:
                            continue
            
            # Fallback: look for any hw:0, device
            for i, device in enumerate(devices):
                if (device['max_input_channels'] > 0 and 
                    'hw:0,' in str(device)):
                    
                    default_rate = int(device['default_samplerate'])
                    print(f"[USB MIC] Found card 0 device {i}: {device['name']} at {default_rate}Hz")
                    return i, default_rate
            
            print("[USB MIC] No USB microphone found, using default")
            return None, None
            
        except Exception as e:
            print(f"[USB MIC] Detection failed: {e}")
            return None, None
    
    def _setup_logging(self, log_path):
        """Setup logging configuration."""
        log_path = log_path or os.path.join(self.base_dir, "logs", "streaming_mic_manager.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Create a logger specific to this manager
        self.logger = logging.getLogger(f"StreamingMicManager_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Only add handler if not already present
        if not self.logger.handlers:
            handler = logging.FileHandler(log_path)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def acquire(self):
        """Acquire exclusive access to the microphone."""
        StreamingMicManager._lock.acquire()
        try:
            self._file_lock = open(self._file_lock_path, 'w')
            fcntl.flock(self._file_lock, fcntl.LOCK_EX)
            self._acquired = True
            self.logger.info("StreamingMicManager acquired (file lock)")
            return True
        except Exception as e:
            StreamingMicManager._lock.release()
            self.logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def release(self):
        """Release microphone access."""
        self.stop_streaming()
        self._acquired = False
        if self._file_lock:
            fcntl.flock(self._file_lock, fcntl.LOCK_UN)
            self._file_lock.close()
            self._file_lock = None
        StreamingMicManager._lock.release()
        self.logger.info("StreamingMicManager released (file lock)")
    
    def calibrate_noise_floor(self, duration=None):
        """
        Calibrate the noise floor for auto-adjusting VAD threshold.
        
        Args:
            duration: Calibration duration in seconds (default: self.calibration_duration)
        """
        if not self._acquired:
            raise RuntimeError('Must acquire before calibrating')
        
        duration = duration or self.calibration_duration
        self.logger.info(f"Calibrating noise floor for {duration:.1f} seconds...")
        print(f"[CALIBRATION] Measuring background noise for {duration:.1f} seconds - please be quiet...")
        
        amplitudes = []
        samples_needed = int(duration * self.sample_rate / self.chunk_size)
        
        def calibration_callback(indata, frames, time, status):
            if status:
                self.logger.warning(f"Calibration audio status: {status}")
            amplitude = np.abs(indata).mean() * 1000  # Scale float32 to reasonable range
            amplitudes.append(amplitude)
        
        # Record background noise
        stream = sd.InputStream(
            callback=calibration_callback,
            device=self.audio_device,
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.chunk_size,
            dtype='float32'
        )
        
        with stream:
            time.sleep(duration)
        
        if amplitudes:
            self.noise_floor = np.mean(amplitudes)
            # Set threshold to 5x noise floor, with reasonable bounds for normal speech
            # Normal speech should be 20-100, loud speech 100-500
            raw_threshold = self.noise_floor * 5.0
            self.vad_threshold = max(min(raw_threshold, 150.0), 15.0)  # Keep between 15-150
            self._last_calibration = datetime.now()
            
            self.logger.info(f"Calibration complete - Noise floor: {self.noise_floor:.1f}, VAD threshold: {self.vad_threshold:.1f}")
            print(f"[CALIBRATION] Complete - Background: {self.noise_floor:.1f}, Trigger threshold: {self.vad_threshold:.1f}")
            print(f"[CALIBRATION] Speak normally (should be 20-100), loud speech (100-500)")
        else:
            self.logger.error("Calibration failed - no audio data received")
            print("[CALIBRATION] Failed - no audio data received")
    
    def auto_recalibrate_if_needed(self):
        """Automatically recalibrate if enough time has passed."""
        if (self._last_calibration is None or 
            datetime.now() - self._last_calibration > self._calibration_interval):
            
            # Use recent amplitude history for quick recalibration
            if len(self._amplitude_history) >= 50:
                recent_amplitudes = list(self._amplitude_history)[-50:]
                # Use the 25th percentile as noise floor (assuming most time is silence)
                self.noise_floor = np.percentile(recent_amplitudes, 25)
                raw_threshold = self.noise_floor * 5.0
                self.vad_threshold = max(min(raw_threshold, 150.0), 15.0)  # Keep reasonable for speech
                self._last_calibration = datetime.now()
                
                self.logger.info(f"Auto-recalibrated - Noise floor: {self.noise_floor:.1f}, VAD threshold: {self.vad_threshold:.1f}")
                print(f"[AUTO-CAL] Updated - Background: {self.noise_floor:.1f}, Trigger: {self.vad_threshold:.1f}")
    
    def start_streaming(self, enable_vad=True):
        """
        Start streaming audio with optional voice activity detection.
        
        Args:
            enable_vad: Enable voice activity detection for automatic speech detection
        """
        if not self._acquired:
            raise RuntimeError('Must acquire before streaming')
        
        if self._streaming:
            self.logger.warning("Already streaming")
            return
        
        self.logger.info("Starting audio streaming with real-time processing")
        print("[STREAMING] Starting real-time audio processing...")
        
        # Calibrate if not done recently
        if enable_vad and self._last_calibration is None:
            self.calibrate_noise_floor()
        
        self._stop_requested = False
        self._streaming = True
        
        # Start audio streaming thread
        self._stream_thread = threading.Thread(
            target=self._audio_stream_worker,
            args=(enable_vad,),
            daemon=True
        )
        self._stream_thread.start()
        
        # Start audio processing thread
        self._processing_thread = threading.Thread(
            target=self._audio_processing_worker,
            args=(enable_vad,),
            daemon=True
        )
        self._processing_thread.start()
    
    def stop_streaming(self):
        """Stop audio streaming."""
        if not self._streaming:
            return
        
        self.logger.info("Stopping audio streaming")
        print("[STREAMING] Stopping...")
        
        self._stop_requested = True
        self._streaming = False
        
        # Wait for threads to finish
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=2.0)
        
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2.0)
        
        # Clear the audio queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def _audio_stream_worker(self, enable_vad):
        """Worker thread for audio streaming."""
        def audio_callback(indata, frames, time, status):
            if status:
                self.logger.warning(f"Audio stream status: {status}")
            
            if not self._stop_requested:
                # Convert to int16 and put in queue
                audio_data = (indata * 32767).astype(np.int16)
                try:
                    self._audio_queue.put(audio_data, block=False)
                except queue.Full:
                    # Drop oldest data if queue is full
                    try:
                        self._audio_queue.get_nowait()
                        self._audio_queue.put(audio_data, block=False)
                    except queue.Empty:
                        pass
        
        try:
            stream = sd.InputStream(
                callback=audio_callback,
                device=self.audio_device,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.chunk_size,
                dtype='float32'
            )
            
            with stream:
                self.logger.info(f"Audio stream started - Device: {stream.device}, SR: {self.sample_rate}Hz")
                while not self._stop_requested:
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Audio streaming error: {e}")
            print(f"[ERROR] Audio streaming failed: {e}")
        finally:
            self.logger.info("Audio stream stopped")
    
    def _audio_processing_worker(self, enable_vad):
        """Worker thread for processing audio chunks and VAD."""
        speech_active = False
        speech_start_time = None
        last_speech_time = None
        audio_buffer = []
        
        while not self._stop_requested:
            try:
                # Get audio chunk with timeout
                audio_chunk = self._audio_queue.get(timeout=0.1)
                current_time = time.time()
                
                # Calculate amplitude - convert int16 back to reasonable scale
                amplitude = np.abs(audio_chunk).mean()  # This is int16 data
                # Scale to match our threshold expectations (0-1000 range typically)
                amplitude_scaled = amplitude / 32.767  # Scale int16 to 0-1000 range
                self._amplitude_history.append(amplitude_scaled)
                
                # Call amplitude callback for real-time monitoring
                if self.on_amplitude_update:
                    try:
                        self.on_amplitude_update(amplitude_scaled)
                    except Exception as e:
                        self.logger.error(f"Amplitude callback error: {e}")
                
                # Always add to pre-recording buffer
                self.pre_recording_buffer.append(audio_chunk)
                
                # Voice Activity Detection with hysteresis
                if enable_vad:
                    # Use different thresholds for starting vs continuing speech
                    start_threshold = self.vad_threshold
                    continue_threshold = self.vad_threshold * 0.4  # Lower threshold for continuing
                    
                    if not speech_active:
                        # Need to exceed start threshold to begin speech
                        is_speech = amplitude_scaled > start_threshold
                    else:
                        # Only need to exceed continue threshold to keep going
                        is_speech = amplitude_scaled > continue_threshold
                    
                    if is_speech:
                        if not speech_active:
                            # Speech just started - include pre-recording buffer
                            speech_active = True
                            speech_start_time = current_time
                            
                            # Start with pre-recorded audio to capture speech beginning
                            audio_buffer = list(self.pre_recording_buffer) + [audio_chunk]
                            
                            if self.on_speech_start:
                                try:
                                    self.on_speech_start(amplitude_scaled)
                                except Exception as e:
                                    self.logger.error(f"Speech start callback error: {e}")
                            
                            self.logger.info(f"Speech detected (amplitude: {amplitude_scaled:.1f}) with pre-buffer")
                            print(f"[SPEECH] Started (level: {amplitude_scaled:.1f}) with {len(self.pre_recording_buffer)} pre-chunks")
                        else:
                            # Continue speech
                            audio_buffer.append(audio_chunk)
                        
                        last_speech_time = current_time
                    
                    elif speech_active:
                        # In silence during speech - add chunk but check duration
                        audio_buffer.append(audio_chunk)
                        silence_duration = current_time - last_speech_time
                        total_duration = current_time - speech_start_time
                        
                        # End recording if silence too long OR recording too long
                        should_end = (silence_duration >= self.max_silence_duration or 
                                    total_duration >= self.max_recording_duration)
                        
                        if should_end:
                            # Speech ended
                            speech_duration = current_time - speech_start_time
                            
                            if speech_duration >= self.min_speech_duration:
                                # Valid speech segment
                                audio_data = np.concatenate(audio_buffer) if audio_buffer else None
                                
                                if self.on_speech_end:
                                    try:
                                        self.on_speech_end(audio_data, speech_duration)
                                    except Exception as e:
                                        self.logger.error(f"Speech end callback error: {e}")
                                
                                reason = "max length" if total_duration >= self.max_recording_duration else "silence"
                                self.logger.info(f"Speech ended (duration: {speech_duration:.2f}s, reason: {reason})")
                                print(f"[SPEECH] Ended (duration: {speech_duration:.2f}s, reason: {reason})")
                            else:
                                self.logger.debug(f"Speech too short: {speech_duration:.2f}s")
                            
                            speech_active = False
                            audio_buffer = []
                
                # Call chunk callback for custom processing
                if self.on_audio_chunk:
                    try:
                        self.on_audio_chunk(audio_chunk, amplitude)
                    except Exception as e:
                        self.logger.error(f"Audio chunk callback error: {e}")
                
                # Auto-recalibrate periodically
                if enable_vad and len(self._amplitude_history) % 50 == 0:
                    self.auto_recalibrate_if_needed()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Audio processing error: {e}")
    
    def get_current_amplitude(self):
        """Get the most recent amplitude reading."""
        if self._amplitude_history:
            return self._amplitude_history[-1]
        return 0.0
    
    def get_vad_stats(self):
        """Get current VAD statistics."""
        return {
            'noise_floor': self.noise_floor,
            'vad_threshold': self.vad_threshold,
            'current_amplitude': self.get_current_amplitude(),
            'last_calibration': self._last_calibration.isoformat() if self._last_calibration else None,
            'streaming': self._streaming
        }
    
    def set_vad_parameters(self, threshold=None, min_speech_duration=None, max_silence_duration=None):
        """
        Update VAD parameters.
        
        Args:
            threshold: Voice activity threshold (None to keep current)
            min_speech_duration: Minimum speech duration in seconds
            max_silence_duration: Maximum silence duration in seconds
        """
        if threshold is not None:
            self.vad_threshold = threshold
            self.logger.info(f"VAD threshold updated to {threshold}")
        
        if min_speech_duration is not None:
            self.min_speech_duration = min_speech_duration
            self.logger.info(f"Min speech duration updated to {min_speech_duration}s")
        
        if max_silence_duration is not None:
            self.max_silence_duration = max_silence_duration
            self.logger.info(f"Max silence duration updated to {max_silence_duration}s")
    
    # Legacy compatibility methods
    def record(self, duration=5, filename=None):
        """Legacy file recording method for compatibility."""
        if not self._acquired:
            raise RuntimeError('Must acquire before recording')
        return self._mic.record(duration, filename)
    
    def list_recordings(self):
        """List recorded files."""
        return self._mic.list_recordings()
    
    def prune_recordings(self, max_files=20):
        """Prune old recordings."""
        self._mic.prune_recordings(max_files=max_files)
    
    def get_sound_level(self, duration=1, threshold=500):
        """Legacy method for getting sound level."""
        return self._mic.stream_amplitude(duration=duration, threshold=threshold)