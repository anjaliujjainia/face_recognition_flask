from flask import Flask, Response, jsonify
# from flask.ext.script import Manager
# from flask.ext.migrate import Migrate, MigrateCommand
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from flask_restful import Resource, Api, reqparse
import werkzeug
from werkzeug.utils import secure_filename
import os
import uuid
import numpy as np

import logging

import face_recognition
from PIL import Image
from skimage import io
import cv2
from urllib.request import urlopen
import pdb
import hashlib

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:test@localhost/face_recognition_db"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:hello123@localhost/face_recognition_db"
api = Api(app)

from models import db  # <-- this needs to be placed after app is created
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
# manager.add_command('runserver', Server(host='localhost', port=8080, debug=True))
from models import Person, Face, Photo

DIR = os.path.abspath(os.path.dirname(__file__))
LOCATION = os.path.join(DIR, 'static/images')
FACE_LOCATION = os.path.join(DIR, 'static/faces')
app.config['LOCATION'] = LOCATION
app.config['FACE_LOCATION'] = FACE_LOCATION
known_face_encodings = []
known_face_names = []
known_person_faces = []
known_person_photos = []

@app.route("/")
def index():
    return Response("Hello World!"), 200

def getFaceEncoding(image):
    face = cv2.imread(image)
    return face_recognition.face_encodings(face)[0]
# Models : 
#           Photo(image_hash, image_path, added_on, captions)
#           Face(f_uuid, photo, encoding, person, location_top, location_bottom, location_left,     location_right, is_labeled=False)
#           Person(mean_encoding, name, cluster_id)
#           AlbumUser

def getImageFromURL(url):
    req = urlopen(url)
    # arr = np.asarray(bytearray(req), dtype=np.uint8)
    img = io.imread(url)
    cv2.imshow("1.jpg",img)
    return img

def getMd5Sum(url, max_file_size=100*1024*1024):
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

def save_face_img(faceId, personFace):
    filename = faceId  + ".jpeg"
    face_img_path = os.path.join(app.config['FACE_LOCATION'], filename)

    # changing the color format of personFace from BGR to RGB 
    personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
    
    # saving the thumbnail of the face at img_path
    cv2.imwrite(face_img_path, personFace)
    # cv2.imshow("12.jpg", personFace)

def generate_md5(image_path):
    hash_md5 = hashlib.md5()
    with open(self.image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

class RecognizeFace(Resource):
    def post(self):
        # Making request for image
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=werkzeug.FileStorage, location='files')
        # parse.add_argument('image', type = str) # for url image
        parse.add_argument('caption', type = str)
        args = parse.parse_args()
        pdb.set_trace()
        if args['image']:
            img = args['image']
            # img = getImageFromURL(img) # for url image
            image = face_recognition.load_image_file(img)
            caption = args['caption']
            
            person_query = db.session.query(Person).all()
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
            image_path = os.path.join(app.config['LOCATION'], photoId+".jpeg")
            image_hash = generate_md5(image_path)
            # img_path = img # for url image
            photoObj = Photo(image_path, image_hash, caption)
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
                    personObj = db.session.query(Person).filter_by(id=matched_id).first()
                    personObj.update_average_face_encoding(faceEncoding)
                    faceNames.append(personObj.name)
                else:
                    name = "unknown"
                    personObj = Person(faceEncoding, name)
                    db.session.add(personObj)
                    db.session.commit()
                
                # Make a face object and save to database with unknown name
                top, right, bottom, left = faceLocations[i]
                personFace = image[top:bottom, left:right]
                faceObj = Face(faceId, photoObj.id, faceEncoding, personObj.id, top, bottom, left , right)
                db.session.add(faceObj)
                db.session.commit()
                save_face_img(faceId, personFace)

            if len(faceNames) == 0:
                return jsonify({"status": 200, "message": "No Known Faces Found."})
            return jsonify({"status": 200, "message": "Faces Found.", "known_faces": str(faceNames)})
        else:
            return jsonify({"status": 406, "message": "Please Provide Image."})
# Returns all the faces
api.add_resource(RecognizeFace, '/api/photo/get_faces')

'''
class FindFace(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        # reading image
        parse.add_argument('image', type=werkzeug.FileStorage, location='files')
        # parse.add_argument('image', type = str) # for url image

        # reading the post request into dict
        args = parse.parse_args()
        message = ""
        if args['image']:
            image = face_recognition.load_image_file(args['image'])
            faceLocations = face_recognition.face_locations(image)
            query = db.session.query(Person).all()
            knownFaceEncodings = [_.mean_encoding for _ in query]
            knownFaceID = [_.id for _ in query]
            # faceEncodings = face_recognition.face_encodings(image, faceLocations)
            photoId = str(uuid.uuid4())
            for face in faceLocations:
                top, right, bottom, left = face
                personFace = image[top:bottom, left:right]
                faceId = str(uuid.uuid4())
                filename = faceId  + ".jpeg"
                img_path = os.path.join(app.config['LOCATION'], filename)
                # changing the color format of personFace from BGR to RGB 
                personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
                # saving the thumbnail of the face at img_path
                cv2.imwrite(img_path, personFace)
                # face encoding
                encoding = face_recognition.face_encodings(face_recognition.load_image_file(img_path))[0]
                # faceId = str(uuid.uuid4())
                # for faceEncoding in faceEncodings:
                matches = face_recognition.compare_faces(knownFaceEncodings, encoding)

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    firstMatchIndex = matches.index(True)
                    ID = knownFaceID[firstMatchIndex]
                    person = Face(faceId, photoId, list(encoding), ID)
                    message += "Id {0} added, ".format(ID)
                else:
                    # clusterId = query[0].cluster_id + 1
                    cluster = Cluster(encoding, "Unknown")
                    db.session.add(cluster)
                    db.session.commit()
                    person = Person(faceId, photoId, list(encoding), cluster.cluster_id)
                    # db.session.add(person) === Callback to check if the object is created
                    message += "New Id {0} added, ".format(cluster.cluster_id)
                    # db.session.commit()
                
                db.session.add(person)
                db.session.commit()
                
            #     filename = faceId  + ".jpeg"
            #     img_path = os.path.join(app.config['LOCATION'], filename)
            #     personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
            #     cv2.imwrite(img_path, personFace)
            return jsonify({"status": 200, "message": message})
        else:
            return jsonify({"status": 406, "message": "Provide Image."})
# api.add_resource(FindFace, '/api/find_face') 
api.add_resource(FindFace, '/api/photo/find_face') 



class GetAllFaces(Resource):
    def get(self):
        query = db.session.query(Cluster).all()
        newFaces = []
        recognizedFaces = []
        for cluster in query:
            if 'unknown' in cluster.cluster_name:
                newFaces.append(cluster.cluster_name)
            else:
                personDict = {}
                persons = db.session.query(Person).filter_by(cluster_id=cluster.cluster_id).all()
                personDict['face_name'] = cluster.cluster_name
                faceImages = [i.photo_id for i in persons]
                personDict['face_images'] = faceImages
                recognizedFaces.append(personDict)
        return jsonify({"new_faces": newFaces, "recognized_faces": recognizedFaces})

api.add_resource(GetAllFaces, '/api/get_all_faces')

class GetData(Resource):
    def get(self):
        persons = db.session.query(Person).all()
        personDict = {}
        for person in persons:
            if person.face_name != 'unknown':
                known_face_encodings.append(person.face_embedding)
                known_face_name.append(person.face_name)
                known_person_faces.append(person.face_id)
                known_person_photos.append(person.photo_id)
            personList = []
            personList.append(person.face_name)
            personList.append(person.face_id)
            personList.append(person.photo_id)
            personList.append(person.face_embedding)
            personDict[person.face_name] = personList
        return jsonify({"persons": str(persons), "person": str(personDict), "Length": str(len(personList))})
api.add_resource(GetData, '/api/getall')
'''
class GetPersonFacesForClass(Resource):
    # in agrs a class_id is given
    def get(self, class_id):

        return jsonify({"class_id": class_id})
api.add_resource(GetPersonFacesForClass, '/api/get_data_by_class/<int:class_id>')

if __name__ == "__main__":
    manager.run()
