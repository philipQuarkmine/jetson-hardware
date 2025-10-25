
# LED Manager for Jetson Orin Nano


import threading
import time

from Libs.CubeNanoLib import CubeNano


class LEDManager:
	_lock = threading.Lock()
	def __init__(self, bus=7, delay=0.008):
		self._cube = CubeNano(i2c_bus=bus, delay=delay)
		self._acquired = False

	def acquire(self):
		LEDManager._lock.acquire()
		self._acquired = True

	def release(self):
		self._acquired = False
		LEDManager._lock.release()

	def set_effect(self, effect=1, speed=2, color=6):
		if not self._acquired:
			raise RuntimeError("Must acquire before setting effect")
		self._cube.set_RGB_Effect(effect)
		self._cube.set_RGB_Speed(speed)
		self._cube.set_RGB_Color(color)

	def set_manual_rgb(self, r, g, b, index=255):
		if not self._acquired:
			raise RuntimeError("Must acquire before setting color")
		self._cube.set_Single_Color(index, r, g, b)

	def lights_off(self):
		if not self._acquired:
			raise RuntimeError("Must acquire before turning off")
		self._cube.set_RGB_Effect(0)
		self._cube.set_Single_Color(255, 0, 0, 0)

	def chase_led(self, color=(255,0,0), delay=0.1, cycles=1, num_leds=14):
		if not self._acquired:
			raise RuntimeError("Must acquire before chasing LED")
		for _ in range(cycles):
			for idx in range(num_leds):
				self.set_manual_rgb(*color, index=idx)
				time.sleep(delay)
