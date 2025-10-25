import time

from Managers.OLED_Manager import OLEDManager

oled = OLEDManager()
oled.acquire()
print("Testing OLED: Scroll message")
oled.show_message_scroll("Hello Jetson!", size=32, speed=5, duration=10)
print("Message should be scrolling for 10 seconds...")
print("Testing OLED: Clear display")
oled.clear()
oled.release()
print("OLED test complete.")
