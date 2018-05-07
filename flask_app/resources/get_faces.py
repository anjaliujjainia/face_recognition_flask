from flask import request
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db, app

import werkzeug
import pdb
import face_recognition
import os
import uuid
import cv2


photo_location = app.config['LOCATION']
face_location = app.config['FACE_LOCATION']


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
        if args['image']:
            img = args['image']
            # img = getImageFromURL(img) # for url image
            image = face_recognition.load_image_file(img)
            caption = args['caption']
            
            person_query = db.session.query(Model.Person).all()
            knownFaceEncodings = [_.mean_encoding for _ in person_query]
            knownFaceIds = [_.id for _ in person_query]
            
            faceLocations = face_recognition.face_locations(image)
            faceEncodings = face_recognition.face_encodings(image, faceLocations)
            
            faceNames = []

            # -------- Photo ---------
            photoId = str(uuid.uuid4())
            # URL of the image from the server
            # img_hash = getMd5Sum(img) # for url image
            # image_hash = str(uuid.uuid4())

            # url of image from arguments(ruby -------TO DO --------------) 
            image_path = os.path.join(photo_location, photoId+".jpeg")
            image_hash = generate_md5(image_path)
            # img_path = img # for url image
            photoObj = Model.Photo(image_path, image_hash, caption)
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
                    personObj = Model.Person(faceEncoding, name)
                    db.session.add(personObj)
                    db.session.commit()
                
                # Make a face object and save to database with unknown name
                top, right, bottom, left = faceLocations[i]
                personFace = image[top:bottom, left:right]
                faceObj = Model.Face(faceId, photoObj.id, faceEncoding, personObj.id, top, bottom, left , right)
                db.session.add(faceObj) 
                db.session.commit()
                save_face_img(faceId, personFace)

            if len(faceNames) == 0:
                return jsonify({"status": 200, "message": "No Known Faces Found."})

            return jsonify({"status": 200, "message": "Faces Found.", "known_faces": str(faceNames)})
        else:
            return jsonify({"status": 406, "message": "Please Provide Image."})

def save_face_img(faceId, personFace):
    filename = faceId  + ".jpeg"
    face_img_path = os.path.join(face_location, filename)

    # changing the color format of personFace from BGR to RGB 
    personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
    
    # saving the thumbnail of the face at img_path
    cv2.imwrite(face_img_path, personFace)
    # cv2.imshow("12.jpg", personFace)
