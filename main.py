from gpiozero import MotionSensor
from picamera import PiCamera
import time
import cv2
import imutils
import re
from LPR import LPR
import sqlite3
import datetime

camera = PiCamera()
attemps = 1
max_attemps = 20
retries = 1


def detect_movement():
	pir = MotionSensor(4)
	while True:
		pir.wait_for_motion()
		print("Motion Detected")
		take_picture()
		pir.wait_for_no_motion()
		print("Motion stopped")

def take_picture():
	global attemps
	path = "imgs/img.jpg"
	camera.capture(path)
	print("Picture taken. Attemp #" + str(attemps))
	recognize(path)

def open_door():
	print("Opening door..")

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
	init_database()
	begin()