import time

from Managers.LED_Manager import LEDManager

led = LEDManager()
led.acquire()
print("Testing LED: ON (set_effect)")
led.set_effect(effect=1, speed=2, color=6)  # Breathing, medium, white
print("LED should be ON for 10 seconds...")
time.sleep(10)
print("Testing LED: OFF (lights_off)")
led.lights_off()
led.release()
print("LED test complete.")
