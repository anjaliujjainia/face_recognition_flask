import os
import numpy as np
import hashlib
import cv2

from urllib.request import urlopen
from flask_app.app import app

photo_location = app.config['LOCATION']
face_location = app.config['FACE_LOCATION']

# ----------- Generate Image from URL ---------------------
def get_image_from_url(url):
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
