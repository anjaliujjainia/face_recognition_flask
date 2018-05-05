from flask import Flask, Response, jsonify, request, abort
from flask_restful import Resource, Api, reqparse


import logging

import pdb
import hashlib
from flask_sqlalchemy import SQLAlchemy
from instance.config import *

# def create_app(config_name):
app = Flask(__name__)
app.config.from_object('instance.config.DevelopmentConfig')
app.config.from_pyfile('../instance/config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
api = Api(app)

db.init_app(app)

from flask_app.resources.get_faces import GetFaces
from flask_app.resources.get_data_by_class import GetPersonFacesForClass
from flask_app.resources.update_person_details import UpdatePersonDetails

api.add_resource(GetFaces, '/api/photo/get_faces')
api.add_resource(GetPersonFacesForClass, '/api/get_data_by_class/<int:group_id>')
api.add_resource(UpdatePersonDetails, '/api/update_person_details')