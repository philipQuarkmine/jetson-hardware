
import smbus
import time

class CubeNano:
	def __init__(self, i2c_bus=7, delay=0.002, debug=False):
		self.__debug = debug
		self.__delay = delay
		self.__i2c_bus = smbus.SMBus(int(i2c_bus))
		self.__Addr = 0x0E
		self.__REG_FAN = 0x08
		self.__REG_RGB_Effect = 0x04
		self.__REG_RGB_Speed = 0x05
		self.__REG_RGB_Color = 0x06

	def __del__(self):
		print("CubeNano End!")

	def set_Fan(self, state):
		if state > 0:
			state = 1
		try:
			self.__i2c_bus.write_byte_data(self.__Addr, self.__REG_FAN, state)
			if self.__delay > 0:
				time.sleep(self.__delay)
		except:
			if self.__debug:
				print("---set_Fan Error---")

	def set_RGB_Effect(self, effect):
		if effect < 0 or effect > 6:
			effect = 0
		try:
			self.__i2c_bus.write_byte_data(self.__Addr, self.__REG_RGB_Effect, effect)
			if self.__delay > 0:
				time.sleep(self.__delay)
		except:
			if self.__debug:
				print("---set_RGB_Effect Error---")

	def set_RGB_Speed(self, speed):
		if speed < 1 or speed > 3:
			speed = 1
		try:
			self.__i2c_bus.write_byte_data(self.__Addr, self.__REG_RGB_Speed, speed)
			if self.__delay > 0:
				time.sleep(self.__delay)
		except:
			if self.__debug:
				print("---set_RGB_Speed Error---")

	def set_RGB_Color(self, color):
		if color < 0 or color > 6:
			color = 0
		try:
			self.__i2c_bus.write_byte_data(self.__Addr, self.__REG_RGB_Color, color)
			if self.__delay > 0:
				time.sleep(self.__delay)
		except:
			if self.__debug:
				print("---set_RGB_Color Error---")

	def set_Single_Color(self, index, r, g, b):
		try:
			self.__i2c_bus.write_byte_data(self.__Addr, self.__REG_RGB_Effect, 0)
			if self.__delay > 0:
				time.sleep(self.__delay)
			self.__i2c_bus.write_byte_data(self.__Addr, 0x00, int(index)&0xFF)
			if self.__delay > 0:
				time.sleep(self.__delay)
			self.__i2c_bus.write_byte_data(self.__Addr, 0x01, int(r)&0xFF)
			if self.__delay > 0:
				time.sleep(self.__delay)
			self.__i2c_bus.write_byte_data(self.__Addr, 0x02, int(g)&0xFF)
			if self.__delay > 0:
				time.sleep(self.__delay)
			self.__i2c_bus.write_byte_data(self.__Addr, 0x03, int(b)&0xFF)
			if self.__delay > 0:
				time.sleep(self.__delay)
		except:
			if self.__debug:
				print("---set_Single_Color Error---")

	def get_Version(self):
		self.__i2c_bus.write_byte(self.__Addr, 0x00)
		version = self.__i2c_bus.read_byte(self.__Addr)
		return version
