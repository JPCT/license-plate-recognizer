from gpiozero import MotionSensor
from picamera import PiCamera
import time
import cv2
import imutils
import re
from LPR import LPR
import sqlite3
import datetime
import RPi.GPIO as GPIO

camera = PiCamera()
attemps = 1
max_attemps = 20
retries = 1

#Servo config
GPIO.setmode(GPIO.BOARD) #Use Board numerotation mode
GPIO.setwarnings(False) #Disable warnings

#Use pin 12 for PWM signal
pwm_gpio = 12
frequence = 50
GPIO.setup(pwm_gpio, GPIO.OUT)
pwm = GPIO.PWM(pwm_gpio, frequence)

#PIR Sensor config
pir = MotionSensor(4)

#Buzzer Config
GPIO.setwarnings(False)
#GPIO mode selection
#GPIO.setmode(GPIO.BCM)
#Set buzzer - pin 27 as output
buzz=13
GPIO.setup(buzz,GPIO.OUT)

def angle_to_percent (angle) :
    if angle > 180 or angle < 0 :
        return False

    start = 4
    end = 12.5
    ratio = (end - start)/180 #Calcul ratio from angle to percent

    angle_as_percent = angle * ratio

    return start + angle_as_percent

def open_door():
	print("Opening door..")

	#Init at 0°
	pwm.start(angle_to_percent(145))
	time.sleep(1)

	#Go at 90°
	pwm.ChangeDutyCycle(angle_to_percent(55))
	time.sleep(5)

	#Finish at 180°
	pwm.ChangeDutyCycle(angle_to_percent(145))
	
	print("Waiting for no motion...")
	pir.wait_for_no_motion()
	print("Motion Stopped")
	detect_movement()

def alarm():
	i = 1
	while i < 10:
		print("Alarm ringing..." + str(10-i))
		GPIO.output(buzz,GPIO.HIGH)
		time.sleep(1) # Delay in seconds
		GPIO.output(buzz,GPIO.LOW)
		time.sleep(1)
		i += 1
	detect_movement()

def detect_movement():
	print("Waiting for motion...")
	pir.wait_for_motion()
	print("Motion Detected")
	take_picture()

def take_picture():
	global attemps
	path = "imgs/img.jpg"
	camera.capture(path)
	print("Picture taken. Attemp #" + str(attemps))
	recognize(path)

def validate_plate(plate):
	global attemps, retries
	# Connecting to sqlite
	# connection object
	connection_obj = sqlite3.connect('plates.db')
	
	# cursor object
	cursor_obj = connection_obj.cursor()

	cursor_obj.execute("SELECT * FROM PLATES WHERE Plate = '" + plate + "'")
	plate_obj = cursor_obj.fetchone()

	if plate_obj != None:
		print("Welcome " + plate_obj[1] + " " + plate_obj[2])
		#UPDATE Query
		updateQuery = '''UPDATE PLATES SET Last_Access = ? WHERE Plate = ?'''

		#UPDATE records.
		update_obj = (datetime.datetime.now(), plate)
		cursor_obj.execute(updateQuery, update_obj)

		connection_obj.commit()
		connection_obj.close()

		open_door()
	else:
		connection_obj.commit()
		connection_obj.close()
		print("Plate " + plate + " not found")
		if retries < 3:
			attemps = 1
			retries += 1
			print("Retrying... " + str(retries))
			take_picture()
		else:
			retries = 1
			alarm()

def validate_characters(plate):
	global attemps
	pat = re.compile(r"([A-Z])([A-Z])([A-Z])([0-9])([0-9])([0-9])")
	plate = plate.strip()
	
	if re.fullmatch(pat, plate):
		attemps = 1
		print(plate)
		validate_plate(plate)
	elif attemps < max_attemps:
		attemps += 1
		take_picture()
	attemps = 1
	detect_movement()
	

def recognize(path):
	lpr = LPR()
	image = cv2.imread(path)
	image = imutils.resize(image, height=500, width=500 )
	plate = lpr.read_license(image)
	validate_characters(plate)

def begin():
	detect_movement()


def init_database():
	# Connecting to sqlite
	# connection object
	connection_obj = sqlite3.connect('plates.db')
	
	# cursor object
	cursor_obj = connection_obj.cursor()
	
	# Drop the GEEK table if already exists.
	cursor_obj.execute("DROP TABLE IF EXISTS PLATES")
	
	# Creating table
	table = """ CREATE TABLE PLATES (
				Plate VARCHAR(255) PRIMARY KEY,
				Owner_First_Name CHAR(25) NOT NULL,
				Owner_Last_Name CHAR(25),
				Last_Access timestamp
			); """
	
	cursor_obj.execute(table)
	
	print("Table is Created")

	currentDateTime = datetime.datetime.now()

	#INSERT Query
	insertQuery = '''INSERT INTO PLATES VALUES (?, ?, ?, ?)'''

	#INSERT records.
	cursor_obj.execute(insertQuery, ('UER689','Juan Sebastian', 'Mejia', currentDateTime))

	connection_obj.commit()
	
	# Close the connection
	connection_obj.close()

if __name__ == '__main__':
	GPIO.output(buzz,GPIO.LOW)
	pwm.start(angle_to_percent(145))
	init_database()
	begin()