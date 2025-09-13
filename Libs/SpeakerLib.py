
import os
import subprocess

class SpeakerLib:
	def __init__(self, audio_device=None):
		self.audio_device = audio_device or 'plughw:0,0'

	def play(self, filename='output.wav'):
		if not os.path.isfile(filename):
			print(f"SpeakerLib: File not found: {filename}")
			return False
		cmd = [
			"aplay",
			"-D", self.audio_device,
			filename
		]
		try:
			subprocess.run(cmd, check=True)
			return True
		except subprocess.CalledProcessError as e:
			print(f"SpeakerLib: aplay failed: {e}")
			return False

	def stream(self):
		pass
