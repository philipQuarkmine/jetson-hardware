
import os
import subprocess
import time
from datetime import datetime

import numpy as np
try:
	import sounddevice as sd
except ImportError:
	sd = None

class MicLib:
	def __init__(self, base_dir=None, audio_device=None):
		self.base_dir = base_dir or os.getcwd()
		self.recordings_dir = os.path.join(self.base_dir, "recordings")
		os.makedirs(self.recordings_dir, exist_ok=True)
		self.audio_device = audio_device or 'plughw:0,0'

	def make_arecord_cmd(self, out_path, duration):
		return [
			"arecord",
			"-D", self.audio_device,
			"-f", "S16_LE",
			"-c", "1",
			"-r", "16000",
			"-d", str(duration),
			"-t", "wav",
			out_path,
		]

	def record(self, duration=5, filename=None):
		ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
		filename = filename or f"rec_{ts}.wav"
		out_path = os.path.join(self.recordings_dir, filename)
		cmd = self.make_arecord_cmd(out_path, duration)
		try:
			subprocess.run(cmd, check=True)
			return out_path
		except subprocess.CalledProcessError as e:
			print(f"arecord failed: {e}")
			time.sleep(2)
			return None

	def list_recordings(self):
		files = [f for f in os.listdir(self.recordings_dir) if f.lower().endswith('.wav')]
		files.sort()
		return files

	def prune_recordings(self, max_files=20):
		files = self.list_recordings()
		if len(files) <= max_files:
			return
		to_remove = files[: len(files) - max_files]
		for fn in to_remove:
			path = os.path.join(self.recordings_dir, fn)
			try:
				os.remove(path)
			except Exception as e:
				print(f"Failed to remove {path}: {e}")

	def stream_amplitude(self, duration=1, samplerate=44100, threshold=500):
		"""
		Streams audio for `duration` seconds and returns True if sound level exceeds threshold.
		Returns average amplitude.
		"""
		if sd is None:
			raise RuntimeError("sounddevice is not installed")
		def callback(indata, frames, time, status):
			pass  # We use blocking read below
		audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
		sd.wait()
		amplitude = np.abs(audio).mean()
		return amplitude
