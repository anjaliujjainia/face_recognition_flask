'''
image url milega tumhe
or kid id milegi
tumhe return krna h
kuchh iss prakar
"kid_id" : "true/false"
kid_id m whi kid id key jo mein bhejunga tumkko
'''
import pdb
import face_recognition

from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db
from . import utils
class VerifySingleFace(Resource):
	def post(self):
		data = dict(request.get_json(force=True))
		response = jsonify({"status": 406, "message": "Method not allowed with NULL data"})
		if len(data) > 0:
			print("========== We Got The Data ===========")
			ruby_image_id = data["ruby_image_id"]
			image_url = data["image_url"]
			has_kid = data["has_kid"]
			if has_kid:
				kid_id = data["kid_id"]

			# ====== Setting up response ======
			message = {}
			message["image_id"] = ruby_image_id
			message[ruby_image_id] = {}
			message[ruby_image_id]["single_person"] = False

			print(message)
			if has_kid:
				message[ruby_image_id]["kid_id"] = kid_id

			# ====== Loading image ======
			try:
				img = utils.get_image_from_url(image_url) # for url image
			except urllib.error.URLError as err:
				print(err.reason)
				message = err.reason
				print('File Not Found at URL')
			else:
				print('YAY! File Found')
				faceLocations = face_recognition.face_locations(img)
				print(faceLocations)
				if len(faceLocations) == 1:
					# there is only single face
					print("Only One Face Found :D")
					message[ruby_image_id]["single_person"] = True

			print("======== Returning Response =========")
			response = jsonify({"status": 200, "message":message})
		return response


# Code not needed img is already a array of pixels
# name = "test"
# img_local_path = utils.save_image(name, img, who='photo') 

# try:
# 	# image = face_recognition.load_image_file(img_local_path)
# 	# os.remove(img_local_path)
# except FileNotFoundError as err:
# 	print(err)
# 	message = err
# else: