from flask import Flask, Response, jsonify
from flask_restful import Resource, Api, reqparse
import werkzeug
from werkzeug.utils import secure_filename
import os
import uuid

import logging

import face_recognition
from skimage import io
from PIL import Image

app = Flask(__name__)
api = Api(app)
DIR = os.path.abspath(os.path.dirname(__file__))
LOCATION = os.path.join(DIR, 'static/images')
app.config['LOCATION'] = LOCATION

@app.route("/")
def index():
    return Response("Hello World!"), 200


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
            for face in faceLocations:
                top, right, bottom, left = face
                faceData.append((top, right, bottom, left))
                personFace = _[top:bottom, left:right]
                person = Image.fromarray(personFace)
                filename = str(uuid.uuid4()) + ".jpeg"
                person.save(os.path.join(app.config['LOCATION'], filename))
            return jsonify( { 'task': "POST", "no_of_faces": faceCount, "face_data": faceData } )
        else:
            return jsonify( { 'task': "POST Not Found" } )
api.add_resource(ImageApi, '/api')

if __name__ == "__main__":
    app.run(debug=True)
