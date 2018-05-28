from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from flask import request, jsonify, current_app
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db, app
import requests
import os
import cv2
import uuid
import werkzeug
import numpy as np
from PIL import Image
from random import randrange
from skimage import io
import hashlib
import face_recognition
from urllib.request import urlopen
import urllib#.request import urlopen
from werkzeug.utils import secure_filename
import pdb
from . import classify_kid_face 
from . import train_faces

photo_location = app.config['LOCATION']
face_location = app.config['FACE_LOCATION']
# API call at /api/photo_detail_response
url = 'http://192.168.104.87:3001/api/v11/pictures/send_api_end_result'
# url = 'http://192.168.108.210:5000/api/photo_detail_response'


# ----------- Generate Image from URL ---------------------
def getImageFromURL(url):
	# https://github.com/ageitgey/face_recognition/issues/442
	req = urlopen(url)
	arr = np.asarray(bytearray(req.read()), dtype="uint8")
	img = cv2.imdecode(arr, 1)
	# cv2.imshow("1.jpg",img)
	return img

# ----------- save image to local storage ---------------------
def save_image(id, img, who='face'):
	filename = id  + ".jpeg"
	if who == "photo":
		img_path = os.path.join(photo_location, filename)
	else:
		img_path = os.path.join(face_location, filename)

		# changing the color format of Image from BGR to RGB 
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	try:
		# saving the thumbnail of the face at img_path
		# pdb.set_trace()
		if cv2.imwrite(img_path, img):
			return img_path
	except:
		print("Could not save " + who)

# ----------- Generate hash of Photo ---------------------
def generate_md5(image_path):
	hash_md5 = hashlib.md5()
	with open(image_path, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()


##
#
# return {"person_id": {photo_id}}
##
def run(data):
	blah = train_faces.train_faces()
	if len(data) > 0:
		new_prsn_ids = {}
		errorImages = {}
		imagesInDB = []
		for image in data.items():
			# getting post data
			ruby_image_id = image[0]                        #randrange(0, 100)#
			imageUrl = image[1]["url"]
			group_id = image[1]["group_id"]                         #randrange(0, 100)
			print("======Ruby Image Id: " + str(ruby_image_id))
			try:
				img = getImageFromURL(imageUrl) # for url image
			except urllib.error.URLError as err:
				print(err.reason)
				print('File Not Found at URL')
				errorImages[ruby_image_id] = err.reason
			else:
				print('YAY! File Found and we are decoding it now') 
				# ---------------------- SAVING IMAGE -----------------
				photoId = str(uuid.uuid4())
				print("======Flask Image Id: " + str(photoId))
				img_local_path = save_image(photoId, img, who='photo')

				# Hold url of images which were not readable
				try:
					image = face_recognition.load_image_file(img_local_path)
					width, height = image.shape[1], image.shape[0]
					image_hash = generate_md5(img_local_path)
					os.remove(img_local_path)
				except FileNotFoundError as err:
					print(err)
					errorImages[ruby_image_id] = err
					continue
				else:
					# -------- Photo ---------
					photoObj = db.session.query(Model.Photo).filter_by(image_hash=image_hash).first()
					if photoObj:
						# if image with the same hash exist, do not create new person faces
						print("Image Already Exist.")
						imagesInDB.append(imageUrl)
						existing_faces = db.session.query(Model.Face).filter_by(photo=photoObj.id).all()
						for face in existing_faces:
							# person_id = face.person
							print("Returning Face: {0}",format(face.id))
							'''
							if person_id in new_prsn_ids.keys():
								new_prsn_ids[person_id].append(ruby_image_id)
							else:
								new_prsn_ids[person_id]=[ruby_image_id]
							'''

					else:
						# person_query = db.session.query(Model.Person).all()
						# knownFaceEncodings = [_.mean_encoding for _ in person_query]
						# knownFaceIds = [_.id for _ in person_query]
						photoObj = Model.Photo(imageUrl, ruby_image_id, image_hash, "None", group_id)
						db.session.add(photoObj)
						db.session.commit()
						
						
						faceLocations = face_recognition.face_locations(image)
						faceEncodings = face_recognition.face_encodings(image, faceLocations)
						
						
						for i, faceEncoding in enumerate(faceEncodings):
							# matchedFacesBool = face_recognition.compare_faces(knownFaceEncodings, faceEncoding, tolerance=0.4)
							faceId = str(uuid.uuid4())

							# Updating person face
							top, right, bottom, left = upgrade_face_boundary(faceLocations[i], height, width)
							face_image = image[top:bottom, left:right]
							
							# Location where face is saved
							saved_face_path = save_image(faceId, face_image, "face")
							face_is_kid = classify_kid_face.is_kid(saved_face_path)
							
							# only if kid face, create new face and person
							if face_is_kid:
								print('===Kid Face===')
								# Known Face
								# if True in matchedFacesBool:
								# 	print("***Person Already Exist***")
								# 	matchedId = knownFaceIds[matchedFacesBool.index(True)]
								# 	personObj = db.session.query(Model.Person).filter_by(id=matchedId).first()
								# 	print("Person Id: " + str(matchedId))
								# 	personObj.update_average_face_encoding(faceEncoding)
								# else:
									# Unknown Face, new unknown person
								print("***New Person***")
								personObj = Model.Person(name="unknown", group_id=group_id)
								db.session.add(personObj)
								db.session.commit()
								person_id = personObj.id

								'''
								if person_id in new_prsn_ids.keys():
									new_prsn_ids[person_id].append(ruby_image_id)
								else:
									new_prsn_ids[person_id]=[ruby_image_id]
								'''

								# face object
								print("Face Image Path: " + saved_face_path)
								faceEncoding = faceEncoding.tobytes().hex()
								faceObj = Model.Face(faceId, photoObj.id, faceEncoding, int(person_id), saved_face_path, top, bottom, left , right)
								db.session.add(faceObj)
								db.session.commit()

								'''
								personObj = db.session.query(Model.Person).filter_by(id=int(person_id)).first()
								if True in matchedFacesBool and len(faceLocations) == 1:
									# if person already exist then update its default_face
									personObj.default_face = faceObj.id
								else:
									# if the person is new, set new face as its default
									personObj.default_face = faceObj.id
								db.session.commit()
								'''
							else:
								print("===Adult Face===")
								# os.remove(saved_face_path)
							
		
		image_response = {
							"error_images": errorImages, 
							"same_images": imagesInDB
							# "people": new_prsn_ids
						}
		print("\nURL: " + url)
		
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
		response = requests.post(url, json=image_response, headers=headers)
		print(response.json())
		print("=========== Task Completed =========")
		return 'Task Completed'


def upgrade_face_boundary(faceLocation, height, width):
	top, right, bottom, left = faceLocation
	top = int(top - (bottom- top)*0.8)
	bottom = int(bottom + (bottom- top)*0.3)
	right = int((right-left)*0.7 + right)
	left = int(left - (right-left)*0.6)
	
	# checking boundaries
	top = 0 if top <= 0 else top
	bottom = height if bottom >= height else bottom
	left = 0 if left <= 0 else left
	right = width if right >= width else right
	return top, right, bottom , left
