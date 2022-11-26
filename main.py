from gpiozero import MotionSensor
from picamera import PiCamera
import time
import cv2
import imutils
import re
from LPR import LPR

camera = PiCamera()
attemps = 1
max_attemps = 20

def detect_movement():
	pir = MotionSensor(4)
	while True:
		pir.wait_for_motion()
		print("Motion Detected")
		take_picture()
		pir.wait_for_no_motion()
		print("Motion stopped")

def take_picture():
	path = "imgs/img.jpg"
	camera.capture(path)
	print("Picture taken. Attemp #" + str(attemps))
	recognize(path)

def validate_characters(plate):
	global attemps
	pat = re.compile(r"([A-Z])([A-Z])([A-Z])([0-9])([0-9])([0-9])")
	plate = plate.strip()
	
	if re.fullmatch(pat, plate):
		attemps = 1
		print(plate)
	elif attemps < max_attemps:
		attemps += 1
		take_picture()
	attemps = 1
	

def recognize(path):
	lpr = LPR()
	image = cv2.imread(path)
	image = imutils.resize(image, height=500, width=500 )
	plate = lpr.read_license(image)
	validate_characters(plate)

def begin():
	detect_movement()

if __name__ == '__main__':
	begin()