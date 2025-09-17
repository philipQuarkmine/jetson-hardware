
import time
import os
from Managers.Speaker_Manager import SpeakerManager

def get_latest_recording():
	rec_dir = "/home/phiip/jetson-hardware/recordings"
	files = [f for f in os.listdir(rec_dir) if f.lower().endswith('.wav')]
	if not files:
		return None
	files.sort()
	return os.path.join(rec_dir, files[-1])

speaker = SpeakerManager()
speaker.acquire()
latest_wav = get_latest_recording()
if latest_wav:
	print(f"Testing Speaker: Play sound ({latest_wav})")
	speaker.play(filename=latest_wav)
	print("Playing sound for 10 seconds...")
	time.sleep(10)
else:
	print("No .wav recording found to play.")
speaker.release()
print("Speaker test complete.")