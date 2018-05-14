from flask import Flask, Response, jsonify, request, abort
from flask_restful import Resource, Api, reqparse


import logging

import pdb
import hashlib
from flask_sqlalchemy import SQLAlchemy
from instance.config import *

DIR = os.path.abspath(os.path.dirname(__file__))
LOCATION = os.path.join(DIR, 'static/images')
MODEL_FOLDER = os.path.join(DIR, 'resources/results')

# FACE_IMAGES_DIR ='/run/user/1000/gvfs/smb-share:server=192.168.108.210,share=shares/face_images/'
# FACE_LOCATION = os.path.join(DIR, 'static/faces')

# def create_app(config_name):
app = Flask(__name__)
app.config.from_object('instance.config.DevelopmentConfig')
app.config.from_pyfile('../instance/config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['LOCATION'] = LOCATION

app.config['FACE_LOCATION'] = FACE_IMAGES_DIR
app.config['MODEL_FOLDER'] = MODEL_FOLDER

db = SQLAlchemy(app)
api = Api(app)

db.init_app(app)

from flask_app.resources.get_faces import GetFaces
from flask_app.resources.get_data_by_class import GetPersonFacesForClass
from flask_app.resources.update_person_details import UpdatePersonDetails
from flask_app.resources.get_person_face_for_kid import GetPersonFaceForKid
from flask_app.resources.manual_tag_kid import ManualTagKid
from flask_app.resources.manual_untag_kid import ManualUntagKid
from flask_app.resources.photo_detail_response import PhotoDetailResponse
from flask_app.resources.get_person_is_kid import GetPersonIsKid

# [POST] send a list of photos and it returns all the known or already existing faces with urls
api.add_resource(GetFaces, '/api/get_faces')
# [GET] Give a group/class id to get all the people in the class with all the photos they belong in
api.add_resource(GetPersonFacesForClass, '/api/get_data_by_class/<int:group_id>')
# [POST] update person details 
api.add_resource(UpdatePersonDetails, '/api/update_person_details')
# [GET]
api.add_resource(GetPersonFaceForKid, '/api/get_person_face_for_kid/<int:kid_id>')
# [POST]
api.add_resource(ManualTagKid, '/api/manual_tag_kid')
# [POST] Manual Untag Person
api.add_resource(ManualUntagKid, '/api/manual_untag_kid')
# [POST] request tp get the data of the worker
api.add_resource(PhotoDetailResponse, '/api/photo_detail_response')
# [POST] Check if person in image is Kid or Adult
api.add_resource(GetPersonIsKid, '/api/get_person_is_kid')
