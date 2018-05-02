from flask import Flask, Response, jsonify
from flask_restful import Resource, Api, reqparse
import werkzeug
from werkzeug.utils import secure_filename
import os
import uuid
import numpy as np

import logging

import face_recognition
from skimage import io
from PIL import Image
import cv2

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:hello123@localhost/face_recognition_db"
api = Api(app)
db = SQLAlchemy(app)

DIR = os.path.abspath(os.path.dirname(__file__))
LOCATION = os.path.join(DIR, 'static/images')
app.config['LOCATION'] = LOCATION
known_face_encodings = []
known_face_names = []
known_person_faces = []
known_person_photos = []

class Person(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    face_id = db.Column(db.String(64))
    photo_id = db.Column(db.String(64))
    face_embedding = db.Column(ARRAY(db.Float))
    cluster_id = db.Column(db.Integer, db.ForeignKey('cluster.cluster_id'))

    def __init__(self, face_id, photo_id, face_embedding, cluster_id):
        self.face_id = face_id
        self.photo_id = photo_id
        self.face_embedding = face_embedding
        self.cluster_id = cluster_id
    
    def __repr__(self):
        return '<Person %r>' % self.face_id

class Cluster(db.Model):
    cluster_id = db.Column(db.Integer, primary_key=True)
    cluster_name = db.Column(db.String(128))
    mean_encoding = db.Column(ARRAY(db.Float))
    def __init__(self, mean_encoding, cluster_name):
        self.cluster_name = cluster_name
        self.mean_encoding = mean_encoding
    
    def __repr__(self):
        return '<Cluster %r>' % self.cluster_id


@app.route("/")
def index():
    return Response("Hello World!"), 200

def getFaceEncoding(image):
    face = cv2.imread(image)
    return face_recognition.face_encodings(face)[0]



class RecognizeFace(Resource):
    def post(self):
        # Making request for image
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=werkzeug.FileStorage, location='files')
        args = parse.parse_args()

        if args['image']:
            image = face_recognition.load_image_file(args['image'])
            faceLocations = face_recognition.face_locations(image)
            query = db.session.query(Cluster).all()
            knownFaceEncodings = [_.mean_encoding for _ in query]
            knownFaceNames = [_.cluster_name for _ in query]
            faceEncodings = face_recognition.face_encodings(image, faceLocations)
            faceNames = []
            for faceEncoding in faceEncodings:
                matches = face_recognition.compare_faces(knownFaceEncodings, faceEncoding)
                name = "Unknown"

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    firstMatchIndex = matches.index(True)
                    name = knownFaceNames[firstMatchIndex]

                faceNames.append(name)
            if len(faceNames) == 0:
                return jsonify({"status": 200, "message": "No Known Faces Found."})
            return jsonify({"status": 200, "message": "Faces Found.", "known_faces": str(faceNames)})
        else:
            return jsonify({"status": 406, "message": "Please Provide Image."})
            
api.add_resource(RecognizeFace, '/api/get_faces')



class FindFace(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=werkzeug.FileStorage, location='files')
        args = parse.parse_args()
        message = ""
        if args['image']:
            image = face_recognition.load_image_file(args['image'])
            faceLocations = face_recognition.face_locations(image)
            query = db.session.query(Cluster).all()
            knownFaceEncodings = [_.mean_encoding for _ in query]
            knownFaceID = [_.cluster_id for _ in query]
            # faceEncodings = face_recognition.face_encodings(image, faceLocations)
            photoId = str(uuid.uuid4())
            for face in faceLocations:
                top, right, bottom, left = face
                personFace = image[top:bottom, left:right]
                faceId = str(uuid.uuid4())
                filename = faceId  + ".jpeg"
                img_path = os.path.join(app.config['LOCATION'], filename)
                personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
                cv2.imwrite(img_path, personFace)
                encoding = face_recognition.face_encodings(face_recognition.load_image_file(img_path))[0]
            # faceId = str(uuid.uuid4())
            # for faceEncoding in faceEncodings:
                matches = face_recognition.compare_faces(knownFaceEncodings, encoding)

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    firstMatchIndex = matches.index(True)
                    ID = knownFaceID[firstMatchIndex]
                    person = Person(faceId, photoId, list(encoding), ID)
                    message += "Id {0} added, ".format(ID)
                else:
                    # clusterId = query[0].cluster_id + 1
                    cluster = Cluster(encoding, "Unknown")
                    db.session.add(cluster)
                    db.session.commit()
                    person = Person(faceId, photoId, list(encoding), cluster.cluster_id)
                    # db.session.add(person)
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
api.add_resource(FindFace, '/api/find_face') 



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












class ImageApi(Resource):
    def get(self):
        return jsonify( { 'task': "GET" } )
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=werkzeug.FileStorage, location='files')
        app.logger.debug("this is a DEBUG message")
        args = parse.parse_args()

        image = args['image']
        if image:
            _ = face_recognition.load_image_file(image)
            faceLocations = face_recognition.face_locations(_)
            faceCount = len(faceLocations)
            faceData = []
            encodings = {}
            photoId = str(uuid.uuid4())
            for face in faceLocations:
                top, right, bottom, left = face
                faceData.append((top, right, bottom, left))
                personFace = _[top:bottom, left:right]
                # person = Image.fromarray(personFace)
                faceId = str(uuid.uuid4())
                filename = faceId  + ".jpeg"
                img_path = os.path.join(app.config['LOCATION'], filename)
                personFace = cv2.cvtColor(personFace, cv2.COLOR_BGR2RGB)
                cv2.imwrite(img_path, personFace)
                encoding = face_recognition.face_encodings(face)[0]

                persons = db.query(Person).all()
                known_face_encodings = [_.face_encodings for _ in persons]
                matches = face_recognition.compare_faces(known_face_encodings, encoding)
                # encoding = getFaceEncoding(img_path)
                # face_id, photo_id, face_name, face_embedding)
                pPerson = Person(faceId, photoId, "unknown", list(encoding))
                db.session.add(pPerson)
                db.session.commit()
                db.session.close()
                # person_encoding = face_recognition.face_encodings(img_path)
                encodings[faceId] = str(len(encoding))
                # person.save(os.path.join(app.config['LOCATION'], filename))
            return jsonify( { 'task': str(matches), "no_of_faces": faceCount, "face_data": faceData, "face_encodings": encodings } )
        else:
            return jsonify( { 'task': "POST Not Found" } )
api.add_resource(ImageApi, '/api')

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


if __name__ == "__main__":
    app.run(debug=True)
