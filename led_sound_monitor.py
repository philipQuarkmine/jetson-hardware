"""
LED Sound Monitor for Jetson Hardware
Continuously reads sound amplitude and sets LED brightness (purple) accordingly.
Stops on Ctrl+C.
"""
import os
import sys
import time

from Managers.LED_Manager import LEDManager
from Managers.Mic_Manager import MicManager


def main():
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "mic_manager.log")
    mic = MicManager(log_path=log_path)
    led = LEDManager()
    print("Starting LED sound monitor. Press Ctrl+C to exit.")
    mic.acquire()
    led.acquire()
    try:
        sample_interval = 1.0
        while True:
            amplitude = mic.get_sound_level(duration=sample_interval, threshold=30)
            if amplitude < 30:
                led.set_manual_rgb(0, 0, 0)
            else:
                brightness = min(max((amplitude - 30) / (180 - 30), 0), 1)
                r = min(int(128 * brightness), 255)
                g = 0
                b = min(int(128 * brightness), 255)
                led.set_manual_rgb(r, g, b)
            # Update every 1 second for clean transitions
            # No need to sleep, as get_sound_level already blocks for sample_interval
    except KeyboardInterrupt:
        print("Exiting LED sound monitor.")
    finally:
        mic.release()
        led.lights_off()
        led.release()

if __name__ == "__main__":
    main()
