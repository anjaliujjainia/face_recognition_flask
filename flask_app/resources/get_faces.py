from flask import request, jsonify
from flask_restful import Resource, reqparse
# from flask_app.Model import Face, Person, Photo
from flask_app import Model
from flask_app.app import db, app

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
        img_path = os.path.join(app.config['LOCATION'], filename)
    else:
        img_path = os.path.join(app.config['FACE_LOCATION'], filename)

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

# import pdb
# Returns all the faces
class GetFaces(Resource):
    def post(self):
        # pdb.set_trace()
        # Making request for image
        data = dict(request.get_json(force=True))
        if len(data) > 0:
            
            faceNames = []
            errorImages = []
            imagesInDB = []
            for image in data.items():
            # INDENTATION START
                ruby_image_id = image[0]                        #randrange(0, 100)#
                imageUrl = image[1]["url"]
                group_id = image[1]["group_id"]                         #randrange(0, 100)
                caption = "RANDOM"                              #args['caption']
                try:
                    img = getImageFromURL(imageUrl) # for url image
                except urllib.error.URLError as err:
                    print(err.reason)
                    pdb.set_trace()
                    print('File Not Found at URL')
                    errorImages.append(ruby_image_id)
                else:
                    print('YAY! File Found and we are decoding it now') 
                    # ---------------------- SAVING IMAGE -----------------
                    photoId = str(uuid.uuid4())
                    img_local_path = save_face_img(photoId, img, who='photo')
                    # Hold url of images which were not readable
                    # errorImages = []
                    try:
                        pdb.set_trace()
                        image = face_recognition.load_image_file(img_local_path)
                        image_hash = generate_md5(img_local_path)
                        os.remove(img_local_path)
                    # except urllib.error.HTTPError as err:
                    except FileNotFoundError as err:
                        pdb.set_trace()
                        print(err)
                        print("Could not load the image from saved Images")
                        errorImages.append(ruby_image_id)
                        continue
                    else:
                        # Getting All rows from person table and making lists of face ids and encodings
                        print("Going in else")
                        pdb.set_trace()
                        person_query = db.session.query(Model.Person).all()
                        knownFaceEncodings = [_.mean_encoding for _ in person_query]
                        knownFaceIds = [_.id for _ in person_query]
                        
                        # Locations of faces in photo
                        faceLocations = face_recognition.face_locations(image)
                        # Encodings of faces in photo
                        faceEncodings = face_recognition.face_encodings(image, faceLocations)

                        # -------- Photo ---------
                        # url of image  generate hash and then delete image from local storage
                        image_path = imageUrl
                        

                        # ruby_image_id, image_hash, image_url, captions, group_id
                        photoObj = db.session.query(Model.Photo).filter_by(image_hash=image_hash).first()
                        if photoObj:
                            imagesInDB.append(imageUrl)
                        else:
                            photoObj = Model.Photo(image_path, ruby_image_id, image_hash, caption, group_id)
                            db.session.add(photoObj)
                            db.session.commit()
                            # ------- End Photo ------
                            
                        for i, faceEncoding in enumerate(faceEncodings):
                            matchedFacesBool = face_recognition.compare_faces(knownFaceEncodings, faceEncoding, tolerance=0.4)
                            faceId = str(uuid.uuid4())
                            # Known Face
                            if True in matchedFacesBool:
                                firstMatchIndex = matchedFacesBool.index(True)
                                matched_id = knownFaceIds[firstMatchIndex]
                                personObj = db.session.query(Model.Person).filter_by(id=matched_id).first()
                                personObj.update_average_face_encoding(faceEncoding)
                                faceNames.append(personObj.name)
                            else:
                                # Unknown Face
                                name = "unknown"
                                personObj = Model.Person(faceEncoding, name, group_id=group_id)
                                db.session.add(personObj)
                                db.session.commit()
                                fetch_person_id = personObj.id
                            
                            # Make a face object and save to database with unknown name
                            top, right, bottom, left = faceLocations[i]
                            personFace = image[top:bottom, left:right]


                            filename = faceId + '.jpg'
                            img_path = os.path.join(face_location, filename)
                            # pdb.set_trace()
                            faceObj = Model.Face(faceId, photoObj.id, faceEncoding, personObj.id, img_path, top, bottom, left , right)
                            db.session.add(faceObj)
                            db.session.commit()

                            # if the person is new, set new face as its default
                            if not True in matchedFacesBool: 
                                personObj = db.session.query(Model.Person).filter_by(id=fetch_person_id).first()
                                personObj.default_face = faceObj.id
                                db.session.commit()
                            
                            save_face_img(faceId, personFace, "face")
                    # INDENTATION END
                # CHECK INDENTATION AND DATA

            if len(faceNames) == 0:
                pdb.set_trace()
                return jsonify({"status": 200, "message": "No Known Faces Found.", "Error Images": errorImages, "Saved Images": imagesInDB})

            return jsonify({"status": 200, "message": "Faces Found.", "known_faces": str(faceNames), "Error Images": errorImages, "Saved Images": imagesInDB})
        else:
            return jsonify({"status": 406, "message": "Please Provide Data."})

'''
{known_faces_match:{ 
        person_id: [images_id_array]
        }, 
    unknown_faces:{
        person_id: [images_id_array]
        }
}
'''