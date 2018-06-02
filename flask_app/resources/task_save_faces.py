from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from flask import request, jsonify, current_app
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db, app
import requests
import os
import uuid
import werkzeug
from PIL import Image
from random import randrange
from skimage import io
import face_recognition

import urllib#.request import urlopen
from werkzeug.utils import secure_filename
import pdb
from . import util_classify_kid_face 
from . import train_faces
from . import utils #get_image_from_url, save_image, generate_md5


photo_location = app.config['LOCATION']
face_location = app.config['FACE_LOCATION']
# API call at /api/photo_detail_response
url = 'http://192.168.104.87:3001/api/v11/pictures/send_api_end_result'
# url = 'http://192.168.108.210:5000/api/photo_detail_response'

##
#
# return {"person_id": {photo_id}}
##
def run(data):
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
				img = utils.get_image_from_url(imageUrl) # for url image
			except urllib.error.URLError as err:
				print(err.reason)
				print('File Not Found at URL')
				errorImages[ruby_image_id] = err.reason
			else:
				print('YAY! File Found and we are decoding it now') 
				# ---------------------- SAVING IMAGE -----------------
				photoId = str(uuid.uuid4())
				print("======Flask Image Id: " + str(photoId))
				img_local_path = utils.save_image(photoId, img, who='photo')

				# Hold url of images which were not readable
				try:
					image = face_recognition.load_image_file(img_local_path)
					width, height = image.shape[1], image.shape[0]
					image_hash = utils.generate_md5(img_local_path)
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
					else:
						photoObj = Model.Photo(imageUrl, ruby_image_id, image_hash, "None", group_id)
						db.session.add(photoObj)
						db.session.commit()
						
						
						faceLocations = face_recognition.face_locations(image)
						faceEncodings = face_recognition.face_encodings(image, faceLocations)
						
						
						for i, faceEncoding in enumerate(faceEncodings):
							faceId = str(uuid.uuid4())

							# Updating person face
							top, right, bottom, left = upgrade_face_boundary(faceLocations[i], height, width)
							face_image = image[top:bottom, left:right]
							
							# Location where face is saved
							saved_face_path = utils.save_image(faceId, face_image, "face")
							face_is_kid = classify_kid_face.is_kid(saved_face_path)
							
							# only if kid face, create new face and person
							if face_is_kid:
								print('===Kid Face===')
								personObj = Model.Person(name="unknown", group_id=group_id)
								db.session.add(personObj)
								db.session.commit()
								person_id = personObj.id

								# face object
								print("Face Image Path: " + saved_face_path)
								faceEncoding = faceEncoding.tobytes().hex()
								faceObj = Model.Face(faceId, photoObj.id, faceEncoding, int(person_id), saved_face_path, top, bottom, left , right)
								db.session.add(faceObj)
								db.session.commit()
							else:
								print("===Adult Face===")
								# os.remove(saved_face_path)
							
		
		image_response = {
							"error_images": errorImages, 
							"same_images": imagesInDB
							# "people": new_prsn_ids
						}
		print("\nURL: " + url)
		train_faces.train()
	
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
