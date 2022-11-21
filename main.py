from gpiozero import MotionSensor
from picamera import PiCamera
import time
import cv2
import imutils
from LPR import LPR

camera = PiCamera()

def detect_movement():
	pir = MotionSensor(4)
	while True:
		pir.wait_for_motion()
		print("Motion Detected")
		take_picture()
		pir.wait_for_no_motion()
		print("Motion stopped")

def take_picture():
	time.sleep(2)
	path = "imgs/img.jpg"
	camera.capture(path)
	print("Picture taken.")
	recognize(path)

def recognize(path):
	lpr = LPR()
	image = cv2.imread(path)
	image = imutils.resize(image, height=500, width=500 )
	print(lpr.read_license(image))

def begin():
	detect_movement()

if __name__ == '__main__':
	begin()