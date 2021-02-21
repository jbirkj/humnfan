#Humi.py

import RPi.GPIO as GPIO


class Humi():


	def __init__(self, hL, p):
		self.currentHumi = 0
		self.currentTemp = 0
		self.humLimit = hL
		self.SSRpin = p
		
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.SSRpin, GPIO.OUT)
		
	def __str__(self):
		return self.currentHumi
		
	def FanControl(self, h):
		self.currentHumi = h
		if self.currentHumi >= self.humLimit:
			self.SetFan(True)
			print("Fan ON")
		else:
			self.SetFan(False)
			print("Fan off")
		
	def SetFan(self, state):	#state must be true/1 or false/0
		GPIO.output(self.SSRpin, state)
		
	def UpdateHumiLimit(self, hL):
		self.humLimit = hL
		print(f'HumLimit updated to {hL}')
		
	 
