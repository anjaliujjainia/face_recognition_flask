from flask import request, jsonify, current_app
from flask_restful import Resource, reqparse
# from flask_app.Model import Face, Person, Photo
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


photo_location = app.config['LOCATION']
face_location = app.config['FACE_LOCATION']
# API call at /api/photo_detail_response
url = 'http://192.168.104.87:3001/api/v11/pictures/send_api_end_result'
# url = 'http://192.168.108.210:5000/api/photo_detail_response'


# ----------- Generate Image from URL ---------------------
def getImageFromURL(url):
	req = urlopen(url)
	arr = np.asarray(bytearray(req.read()), dtype="uint8")
	img = cv2.imdecode(arr, 1)
	# cv2.imshow("1.jpg",img)
	return img

# ----------- save image to local storage ---------------------
def save_face_img(id, img, who='face'):
	filename = id  + ".jpeg"
	if who == "photo":
		img_path = os.path.join(photo_location, filename)
	else:
		img_path = os.path.join(face_location, filename)

		# changing the color format of Image from BGR to RGB 
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	try:
		# saving the thumbnail of the face at img_path
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
	if len(data) > 0:
		new_prsn_ids = {}
		errorImages = {}
		imagesInDB = []
		for image in data.items():
			# getting post data
			ruby_image_id = image[0]                        #randrange(0, 100)#
			imageUrl = image[1]["url"]
			group_id = image[1]["group_id"]                         #randrange(0, 100)

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
				img_local_path = save_face_img(photoId, img, who='photo')
				# Hold url of images which were not readable
				try:
					image = face_recognition.load_image_file(img_local_path)
					image_hash = generate_md5(img_local_path)
					os.remove(img_local_path)
				except FileNotFoundError as err:
					print(err)
					errorImages[ruby_image_id] = err
					continue
				else:
					# -------- Photo ---------
					print("======We sucessfully opened the file!==========")
					photoObj = db.session.query(Model.Photo).filter_by(image_hash=image_hash).first()
					if photoObj:
						# if image with the same hash exist, do not create new person faces
						imagesInDB.append(imageUrl)
						existing_faces = db.session.query(Model.Face).filter_by(photo=photoObj.id).all()
						for face in existing_faces:
							person_id = str(face.person)
							if person_id in new_prsn_ids.keys():
								new_prsn_ids[person_id].append(ruby_image_id)
							else:
								new_prsn_ids[person_id]=[ruby_image_id]

					else:
						person_query = db.session.query(Model.Person).all()
						knownFaceEncodings = [_.mean_encoding for _ in person_query]
						knownFaceIds = [_.id for _ in person_query]
						
						# Locations of faces in photo
						faceLocations = face_recognition.face_locations(image)
						# Encodings of faces in photo
						faceEncodings = face_recognition.face_encodings(image, faceLocations)
						photoObj = Model.Photo(imageUrl, ruby_image_id, image_hash, "None", group_id)
						db.session.add(photoObj)
						db.session.commit()
						# ------- End Photo ------
						
						for i, faceEncoding in enumerate(faceEncodings):
							matchedFacesBool = face_recognition.compare_faces(knownFaceEncodings, faceEncoding, tolerance=0.4)
							faceId = str(uuid.uuid4())
							# Known Face
							if True in matchedFacesBool:
								matchedId = knownFaceIds[matchedFacesBool.index(True)]
								person_id = str(matchedId)
								personObj = db.session.query(Model.Person).filter_by(id=matchedId).first()
								personObj.update_average_face_encoding(faceEncoding)
								db.session.commit()

								if person_id in new_prsn_ids.keys():
									new_prsn_ids[person_id].append(ruby_image_id)
								else:
									new_prsn_ids[person_id]=[ruby_image_id]
							else:
								# Unknown Face, create new unknown person
								name = "unknown"
								newPersonObj = Model.Person(faceEncoding, name, group_id=group_id)
								db.session.add(newPersonObj)
								db.session.commit()
								person_id = str(newPersonObj.id)
								new_prsn_ids[person_id] = [ruby_image_id]
							
							# Make a face object and save to database with unknown name
							top, right, bottom, left = faceLocations[i]
							personFace = image[top:bottom, left:right]


							faceFile = faceId + '.jpg'
							faceImgPath = os.path.join(face_location, faceFile)
							faceObj = Model.Face(faceId, photoObj.id, faceEncoding, int(person_id), faceImgPath, top, bottom, left , right)
							db.session.add(faceObj)
							db.session.commit()

							# if the person is new, set new face as its default
							if not True in matchedFacesBool: 
								personObj = db.session.query(Model.Person).filter_by(id=int(person_id)).first()
								personObj.default_face = faceObj.id
								db.session.commit()
						
							save_face_img(faceId, personFace, "face")
		
		image_response = {
							"error_images": errorImages, 
							"same_images": imagesInDB, 
							"people": new_prsn_ids
						}
		image_res = jsonify(image_response)
		response = requests.post(url, data=image_res.data)
		print(response.status_code)
		print("===========Task Completed==================")
		return 'Task Completed'
	