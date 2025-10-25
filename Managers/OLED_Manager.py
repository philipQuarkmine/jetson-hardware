
# OLED Manager for Jetson Orin Nano


import threading

from Libs.OledLib import OledLib


class OLEDManager:
	_lock = threading.Lock()
	def __init__(self, bus=7, addr=0x3C):
		self._oled = OledLib(i2c_bus=bus, addr=addr)
		self._acquired = False

	def acquire(self):
		OLEDManager._lock.acquire()
		self._acquired = True

	def release(self):
		self._acquired = False
		OLEDManager._lock.release()

	def show_message_static(self, msg, size=32):
		if not self._acquired:
			raise RuntimeError("Must acquire before showing message")
		self._oled.display_text_static(msg, size=size)

	def show_message_scroll(self, msg, size=32, speed=5, duration=None):
		if not self._acquired:
			raise RuntimeError("Must acquire before showing message")
		self._oled.display_text_scroll(msg, size=size, speed=speed, duration=duration)

	def clear(self):
		if not self._acquired:
			raise RuntimeError("Must acquire before clearing")
		self._oled.clear()
