from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

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
import tensorflow as tf
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


# ------ Parameters for Prediction Model ----
model_file = os.path.join(app.config['MODEL_FOLDER'], "output_graph.pb")
label_file = os.path.join(app.config['MODEL_FOLDER'],"output_labels.txt")
input_height = 299
input_width = 299
input_mean = 0
input_std = 255
input_layer = "Placeholder"
output_layer = "final_result"

# ----------- Generate Image from URL ---------------------
def getImageFromURL(url):
	req = urlopen(url)
	arr = np.asarray(bytearray(req.read()), dtype="uint8")
	img = cv2.imdecode(arr, 1)
	# cv2.imshow("1.jpg",img)
	return img

# ----------- save image to local storage ---------------------
def save_image(id, img, who='face'):
	filename = "anjali_" + id  + ".jpeg"
	if who == "photo":
		img_path = os.path.join(photo_location, filename)
	else:
		img_path = os.path.join(face_location, filename)

		# changing the color format of Image from BGR to RGB 
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	try:
		# saving the thumbnail of the face at img_path
		if cv2.imwrite(img_path, img):
			# pdb.set_trace()
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

def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()

    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)

    return graph

# ---------------- Main Tensor ----------------
def read_tensor_from_image_file(file_name, input_height=299, input_width=299, input_mean=0, input_std=255):
    input_name = "file_reader"
    output_name = "normalized"
    file_reader = tf.read_file(file_name, input_name)
    if file_name.endswith(".png"):
        image_reader = tf.image.decode_png(
            file_reader, channels=3, name="png_reader")
    elif file_name.endswith(".gif"):
        image_reader = tf.squeeze(
            tf.image.decode_gif(file_reader, name="gif_reader"))
    elif file_name.endswith(".bmp"):
        image_reader = tf.image.decode_bmp(file_reader, name="bmp_reader")
    else:
        image_reader = tf.image.decode_jpeg(
            file_reader, channels=3, name="jpeg_reader")
    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0)
    resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)

    return result


def load_labels(label_file):
    label = []
    proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
    for l in proto_as_ascii_lines:
        label.append(l.rstrip())
    return label

# ------------- Calling Function -------------
def is_kid(image):
	graph = load_graph(model_file)
	t = read_tensor_from_image_file(
	file_name=image,
	input_height=input_height,
	input_width=input_width,
	input_mean=input_mean,
	input_std=input_std)
		
	input_name = "import/" + input_layer
	output_name = "import/" + output_layer
	input_operation = graph.get_operation_by_name(input_name)
	output_operation = graph.get_operation_by_name(output_name)

	with tf.Session(graph=graph) as sess:
		results = sess.run(output_operation.outputs[0], {
			input_operation.outputs[0]: t
		})
	results = np.squeeze(results)

	top_k = results.argsort()[-5:][::-1]
	labels = load_labels(label_file)
	# Return
	kid = False
	for i in top_k:
		if labels[i] == 'kid' and results[i] >= 0.5:
			kid = True
	return kid


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
				img_local_path = save_image(photoId, img, who='photo')
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
						print("Image Already Exist, Returning Faces.")
						imagesInDB.append(imageUrl)
						existing_faces = db.session.query(Model.Face).filter_by(photo=photoObj.id).all()
						for face in existing_faces:
							person_id = face.person
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
							matchedFacesBool = face_recognition.compare_faces(knownFaceEncodings, faceEncoding, tolerance=0.7)
							faceId = str(uuid.uuid4())
							# Make a face
							top, right, bottom, left = faceLocations[i]
							top = int(top - (bottom- top)*0.8)
							bottom = int(bottom + (bottom- top)*0.3)
							right = int((right-left)*0.7 + right)
							left = int(left - (right-left)*0.6)
							print("###########", top, right, bottom, left )
							personFace = image[top:bottom, left:right]
							
							# Location where face is saved
							saved_face_path = save_image(faceId, personFace, "face")
							face_is_kid = is_kid(saved_face_path)
							
							# Delete adult faces
							if not face_is_kid:
								print("Adult face")
								os.remove(saved_face_path)
							
							# only if kid face, create new face and person
							if face_is_kid:
								print('=========Kid Found!==========')
								# Known Face
								if True in matchedFacesBool:
									print("Person Already Exist")
									matchedId = knownFaceIds[matchedFacesBool.index(True)]
									# person_id = matchedId
									personObj = db.session.query(Model.Person).filter_by(id=matchedId).first()
									personObj.update_average_face_encoding(faceEncoding)
									# ------- He is the only person in the photo, set this face = Default face -------
									if len(faceLocations) == 1:
    										personObj.default_face = faceId
									# db.session.commit()
								else:
									# Unknown Face, new unknown person
									name = "unknown"
									print("New Person")
									personObj = Model.Person(faceEncoding, name, group_id=group_id, is_kid=True)
									db.session.add(personObj)
								db.session.commit()
								person_id = personObj.id

								if person_id in new_prsn_ids.keys():
									new_prsn_ids[person_id].append(ruby_image_id)
								else:
									new_prsn_ids[person_id]=[ruby_image_id]
								# Save face object to database with unknown name
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
						
							
		
		image_response = {
							"error_images": errorImages, 
							"same_images": imagesInDB, 
							"people": new_prsn_ids
						}
		print("=========== Sending Result ==================")
		print("url: " + url)
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
		response = requests.post(url, json=image_response, headers=headers)
		print(response.json())
		print("=========== Task Completed ==================")
		return 'Task Completed'
	