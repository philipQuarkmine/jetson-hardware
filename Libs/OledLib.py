
import os
import time

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
	"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
	"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
	"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
	"/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
	"/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]
MIN_SIZE = 20

def pick_font_path():
	for p in FONT_CANDIDATES:
		if os.path.isfile(p): return p
	return None

def text_bbox(draw, text, font):
	return draw.textbbox((0,0), text, font=font)

def text_size(draw, text, font):
	l,t,r,b = text_bbox(draw, text, font); return (r-l, b-t, t)

def best_font_size_to_fit(path, msg, H, lo=MIN_SIZE, hi=96, margin=2):
	tmp = Image.new("1",(1,1)); d = ImageDraw.Draw(tmp)
	lo = max(lo, MIN_SIZE)
	best, best_h = lo, 0
	while lo <= hi:
		mid = (lo + hi)//2
		try:
			f = ImageFont.truetype(path, mid)
		except: break
		_, h, _ = text_size(d, msg, f)
		if h <= (H - margin):
			best, best_h = mid, h
			lo = mid + 1
		else:
			hi = mid - 1
	return max(MIN_SIZE, best), best_h

class OledLib:
	def __init__(self, i2c_bus=7, addr=0x3C):
		self.serial = i2c(port=i2c_bus, address=addr)
		self.dev = ssd1306(self.serial)
		self.W, self.H = self.dev.width, self.dev.height
		self.font_path = pick_font_path()

	def display_text_static(self, msg, size=32):
		if self.font_path:
			font = ImageFont.truetype(self.font_path, max(MIN_SIZE, size))
		else:
			font = ImageFont.load_default()
		tmp = Image.new("1",(1,1)); dtmp = ImageDraw.Draw(tmp)
		tw, th, t_off = text_size(dtmp, msg, font)
		img = Image.new("1",(self.W,self.H))
		d = ImageDraw.Draw(img)
		x = (self.W - tw)//2
		y = (self.H - th)//2 - t_off
		d.text((x,y), msg, 255, font=font)
		try:
			self.dev.display(img)
		except Exception as e:
			print(f"OLED display error (static): {e}")

	def display_text_scroll(self, msg, size=32, speed=5, duration=None):
		if self.font_path:
			font = ImageFont.truetype(self.font_path, max(MIN_SIZE, size))
		else:
			font = ImageFont.load_default()
		tmp = Image.new("1",(1,1)); dtmp = ImageDraw.Draw(tmp)
		tw, th, t_off = text_size(dtmp, msg, font)
		gap = 24
		canvas_w = max(self.W+1, tw + gap + self.W)
		canvas = Image.new("1",(canvas_w, self.H))
		draw = ImageDraw.Draw(canvas)
		draw.text((self.W, (self.H - th)//2 - t_off), msg, 255, font=font)
		spd = max(1, min(100, speed))
		step_px = 1 + (spd // 15)
		frame_delay = max(0.01, 0.03 - 0.00025*spd)
		start = time.time()
		while True:
			for x in range(0, canvas_w - self.W + 1, step_px):
				window = canvas.crop((x, 0, x + self.W, self.H))
				try:
					self.dev.display(window)
				except Exception as e:
					print(f"OLED display error (scroll): {e}")
				time.sleep(frame_delay)
			if duration is not None and (time.time() - start) > duration:
				break

	def clear(self):
		img = Image.new("1",(self.W,self.H))
		try:
			self.dev.display(img)
		except Exception as e:
			print(f"OLED clear error: {e}")
