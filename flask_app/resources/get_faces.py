from flask import request
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
import face_recognition
from urllib.request import urlopen
from werkzeug.utils import secure_filename

photo_location = app.config['LOCATION']
face_location = app.config['FACE_LOCATION']

def getImageFromURL(url):
    req = urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype="uint8")
    img = cv2.imdecode(arr, -1)
    # cv2.imshow("1.jpg",img)
    return img

def save_face_img(faceId, personFace):
    filename = faceId  + ".jpeg"
    face_img_path = os.path.join(app.config['FACE_LOCATION'], filename)

    # changing the color format of personFace from BGR to RGB 
    personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
    
    # saving the thumbnail of the face at img_path
    cv2.imwrite(face_img_path, personFace)

# Returns all the faces
class GetFaces(Resource):

    def post(self):
        # Making request for image
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=werkzeug.FileStorage, location='files')
        # parse.add_argument('image', type = str) # for url image
        parse.add_argument('caption', type = str)
        args = parse.parse_args()
        # pdb.set_trace()

        # data = dict(request.get_json(force=True))
        if args['image']:#len(data) > 0:
            
            faceNames = []

            # for image in data.items():
            # INDENTATION START
            image_id = randrange(0, 100)#image[0]
            # imageUrl = image[1]["url"]
            group_id = randrange(0, 100)#image[1]["group_id"]

            img = args['image']
            # img = getImageFromURL(imageUrl) # for url image
            image = face_recognition.load_image_file(img)
            caption = "NULL"#args['caption']
            
            person_query = db.session.query(Model.Person).all()
            knownFaceEncodings = [_.mean_encoding for _ in person_query]
            knownFaceIds = [_.id for _ in person_query]
            
            faceLocations = face_recognition.face_locations(image)
            faceEncodings = face_recognition.face_encodings(image, faceLocations)
            
            

            # -------- Photo ---------
            photoId = str(uuid.uuid4())
            # URL of the image from the server
            # img_hash = getMd5Sum(img) # for url image
            # image_hash = str(uuid.uuid4())

            # url of image from arguments(ruby -------TO DO --------------) 
            image_path = "Image Path Required"#os.path.join(app.config['LOCATION'], photoId+".jpeg")
            image_hash = str(randrange(1000, 10000000))#generate_md5(image_path)
            # img_path = img # for url image
            # # # # ruby_id - image_id, image_hash, image_url, captions, group_id
            photoObj = Model.Photo(image_path, image_id, image_hash, caption, group_id)
            db.session.add(photoObj)
            db.session.commit()
            # ------- End Photo ------
            
            for i, faceEncoding in enumerate(faceEncodings):
                matchedFacesBool = face_recognition.compare_faces(knownFaceEncodings, faceEncoding, tolerance=0.4)
                faceId = str(uuid.uuid4())
                # If a match was found in known_face_encodings, just use the first one.
                if True in matchedFacesBool:
                    firstMatchIndex = matchedFacesBool.index(True)
                    matched_id = knownFaceIds[firstMatchIndex]
                    personObj = db.session.query(Model.Person).filter_by(id=matched_id).first()
                    personObj.update_average_face_encoding(faceEncoding)
                    faceNames.append(personObj.name)
                else:
                    name = "unknown"
                    personObj = Model.Person(faceEncoding, name, group_id=group_id)
                    db.session.add(personObj)
                    db.session.commit()
                
                # Make a face object and save to database with unknown name
                top, right, bottom, left = faceLocations[i]
                personFace = image[top:bottom, left:right]
                faceObj = Model.Face(faceId, photoObj.id, faceEncoding, personObj.id, top, bottom, left , right)
                db.session.add(faceObj)
                db.session.commit()
                save_face_img(faceId, personFace)
                # INDENTATION END
            # CHECK INDENTATION AND DATA

            if len(faceNames) == 0:
                return jsonify({"status": 200, "message": "No Known Faces Found."})

            return jsonify({"status": 200, "message": "Faces Found.", "known_faces": str(faceNames)})
        else:
            return jsonify({"status": 406, "message": "Please Provide Data."})

def save_face_img(faceId, personFace):
    filename = faceId  + ".jpeg"
    face_img_path = os.path.join(face_location, filename)

    # changing the color format of personFace from BGR to RGB 
    personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
    
    # saving the thumbnail of the face at img_path
    cv2.imwrite(face_img_path, personFace)
    # cv2.imshow("12.jpg", personFace)
