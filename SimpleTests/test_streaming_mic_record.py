import sys
import time
import wave

import numpy as np

from Managers.Mic_Manager_Streaming import StreamingMicManager

DURATION = 10  # seconds
OUTPUT_FILE = "test_streaming_mic_record.wav"

def main():
    print(f"Recording {DURATION} seconds of audio using StreamingMicManager...")
    mic = StreamingMicManager(channels=1, chunk_size=1024, audio_device=None)
    mic.acquire()
    mic.record(duration=DURATION, filename=OUTPUT_FILE)
    mic.release()
    print(f"Recording complete. Saved audio to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
