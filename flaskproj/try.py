import pdb
import hashlib
import cv2
from urllib.request import urlopen
from io import BytesIO
import numpy as np
from PIL import Image
img = 'https://connectoo.co.il/uploads/pictures/96782/original/5fc9506096c0a9e09c342c049344e265.jpg?1521600668'

def getImageFromURL(url):
	req = urlopen(url)
	file = BytesIO(req.read())
	img = Image.open(file)
	print(str(img))
	return img


def get_remote_md5_sum(url, max_file_size=100*1024*1024):
	remote = urlopen(url)
	hash = hashlib.md5()

	total_read = 0
	while True:
		data = remote.read(4096)
		total_read += 4096

		if not data or total_read > max_file_size:
			break

		hash.update(data)

	return hash.hexdigest()


# img_path = '3.jpeg'
# def generate_md5(img):
# 	hash_md5 = hashlib.md5()
# 	with open(img, "rb") as f:
# 		pdb.set_trace()
# 		for chunk in iter(lambda: f.read(4096), b""):
# 			pdb.set_trace()
# 			hash_md5.update(chunk)
# 	print(hash_md5.hexdigest())


print(get_remote_md5_sum(img))

# generate_md5(img_path)