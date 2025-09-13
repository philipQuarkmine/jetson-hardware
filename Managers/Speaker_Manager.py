
# Speaker Manager for Jetson Orin Nano


import threading
import logging
import signal
import sys
import os
import time
import fcntl
from Libs.SpeakerLib import SpeakerLib

class SpeakerManager:
	_lock = threading.Lock()
	_file_lock_path = '/tmp/speaker_manager.lock'
	_file_lock = None
	def __init__(self, log_path=None, audio_device=None):
		audio_device = audio_device or os.environ.get('SPEAKER_AUDIO_DEVICE', 'plughw:0,0')
		log_path = log_path or os.environ.get('SPEAKER_LOG_PATH', os.path.join(os.getcwd(), "Managers/logs/speaker_manager.log"))
		self._speaker = SpeakerLib(audio_device=audio_device)
		self._acquired = False
		self._setup_logging(log_path)
		self._stop_requested = False

	def _setup_logging(self, log_path):
		log_path = log_path or os.path.join(os.getcwd(), "speaker_manager.log")
		logging.basicConfig(
			filename=log_path,
			level=logging.INFO,
			format='%(asctime)s %(levelname)s %(message)s'
		)

	def acquire(self):
		SpeakerManager._lock.acquire()
		self._file_lock = open(self._file_lock_path, 'w')
		fcntl.flock(self._file_lock, fcntl.LOCK_EX)
		self._acquired = True
		logging.info("SpeakerManager acquired (file lock)")

	def release(self):
		self._acquired = False
		if self._file_lock:
			fcntl.flock(self._file_lock, fcntl.LOCK_UN)
			self._file_lock.close()
			self._file_lock = None
		SpeakerManager._lock.release()
		logging.info("SpeakerManager released (file lock)")

	def play(self, filename='output.wav'):
		if not self._acquired:
			logging.error("Attempted to play without acquiring lock")
			raise RuntimeError('Must acquire before playing')
		logging.info(f"Playing: {filename}")
		try:
			result = self._speaker.play(filename)
			if not result:
				logging.error(f"Playback failed for {filename}")
		except Exception as e:
			logging.error(f"SpeakerManager: Exception during play: {e}")

	def run_background(self, filename, interval=0):
		def _handle(sig, frame):
			logging.info(f"Received signal {sig}, stopping...")
			self._stop_requested = True
		signal.signal(signal.SIGINT, _handle)
		signal.signal(signal.SIGTERM, _handle)
		self.acquire()
		try:
			while not self._stop_requested:
				try:
					self.play(filename=filename)
				except Exception as e:
					logging.error(f"SpeakerManager: Exception in background loop: {e}")
				if interval > 0:
					time.sleep(interval)
				else:
					signal.pause()
		finally:
			self.release()
			logging.info("SpeakerManager background stopped")
