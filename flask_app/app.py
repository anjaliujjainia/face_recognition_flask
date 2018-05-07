from flask import Flask, Response, jsonify, request, abort
from flask_restful import Resource, Api, reqparse


import logging

import pdb
import hashlib
from flask_sqlalchemy import SQLAlchemy
from instance.config import *

DIR = os.path.abspath(os.path.dirname(__file__))
LOCATION = os.path.join(DIR, 'static/images')
FACE_LOCATION = os.path.join(DIR, 'static/faces')

# def create_app(config_name):
app = Flask(__name__)
app.config.from_object('instance.config.DevelopmentConfig')
app.config.from_pyfile('../instance/config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['LOCATION'] = LOCATION
app.config['FACE_LOCATION'] = FACE_LOCATION


db = SQLAlchemy(app)
api = Api(app)

db.init_app(app)

from flask_app.resources.get_faces import GetFaces
from flask_app.resources.get_data_by_class import GetPersonFacesForClass
from flask_app.resources.update_person_details import UpdatePersonDetails
from flask_app.resources.get_person_face_for_kid import GetPersonFaceForKid

# send a list of photos and it returns all the known or already existing faces with urls
api.add_resource(GetFaces, '/api/photo/get_faces')
# Give a group/class id to get all the people in the class with all the photos they belong in
api.add_resource(GetPersonFacesForClass, '/api/get_data_by_class/<int:group_id>')
# update person details 
api.add_resource(UpdatePersonDetails, '/api/update_person_details')
api.add_resource(GetPersonFaceForKid, '/api/get_person_face_for_kid/<int:kid_id>')
