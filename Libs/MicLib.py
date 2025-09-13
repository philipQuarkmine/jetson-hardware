
import os
import subprocess
import time
from datetime import datetime

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

	def stream(self):
		pass
