
# Mic Manager for Jetson Orin Nano


import fcntl
import logging
import os
import signal
import sys
import threading
import time

from Libs.MicLib import MicLib


class MicManager:
	def get_sound_level(self, duration=1, threshold=500):
		"""
		Streams audio for `duration` seconds and returns average amplitude.
		"""
		return self._mic.stream_amplitude(duration=duration, threshold=threshold)
	_lock = threading.Lock()
	_file_lock_path = '/tmp/mic_manager.lock'
	_file_lock = None
	def __init__(self, base_dir=None, audio_device=None, log_path=None):
		base_dir = base_dir or os.environ.get('MIC_BASE_DIR', os.getcwd())
		audio_device = audio_device or os.environ.get('MIC_AUDIO_DEVICE', 'plughw:0,0')
		log_path = log_path or os.environ.get('MIC_LOG_PATH', os.path.join(os.getcwd(), "Managers/logs/mic_manager.log"))
		self._mic = MicLib(base_dir=base_dir, audio_device=audio_device)
		self._acquired = False
		self._setup_logging(log_path)
		self._stop_requested = False

	def _setup_logging(self, log_path):
		log_path = log_path or os.path.join(os.getcwd(), "mic_manager.log")
		logging.basicConfig(
			filename=log_path,
			level=logging.INFO,
			format='%(asctime)s %(levelname)s %(message)s'
		)

	def acquire(self):
		MicManager._lock.acquire()
		self._file_lock = open(self._file_lock_path, 'w')
		fcntl.flock(self._file_lock, fcntl.LOCK_EX)
		self._acquired = True
		logging.info("MicManager acquired (file lock)")

	def release(self):
		self._acquired = False
		if self._file_lock:
			fcntl.flock(self._file_lock, fcntl.LOCK_UN)
			self._file_lock.close()
			self._file_lock = None
		MicManager._lock.release()
		logging.info("MicManager released (file lock)")

	def record(self, duration=5, filename=None):
		if not self._acquired:
			logging.error("Attempted to record without acquiring lock")
			raise RuntimeError('Must acquire before recording')
		logging.info(f"Recording for {duration}s to {filename}")
		try:
			result = self._mic.record(duration, filename)
			if not result:
				logging.error("MicManager: Recording failed")
			return result
		except Exception as e:
			logging.error(f"MicManager: Exception during record: {e}")
			return None

	def list_recordings(self):
		return self._mic.list_recordings()

	def prune_recordings(self, max_files=20):
		self._mic.prune_recordings(max_files=max_files)

	def run_background(self, duration=10, interval=15):
		def _handle(sig, frame):
			logging.info(f"Received signal {sig}, stopping...")
			self._stop_requested = True
		signal.signal(signal.SIGINT, _handle)
		signal.signal(signal.SIGTERM, _handle)
		self.acquire()
		try:
			while not self._stop_requested:
				try:
					path = self.record(duration=duration)
					logging.info(f"Recorded: {path}")
					self.prune_recordings()
				except Exception as e:
					logging.error(f"MicManager: Exception in background loop: {e}")
				signal.pause() if interval == 0 else time.sleep(interval)
		finally:
			self.release()
			logging.info("MicManager background stopped")
