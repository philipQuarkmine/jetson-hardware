import time

from Managers.Mic_Manager import MicManager

mic = MicManager()
mic.acquire()
print("Testing Microphone: Record for 10 seconds")
output_file = mic.record(duration=10)
print(f"Recording saved to: {output_file}")
mic.release()
print("Microphone test complete.")
