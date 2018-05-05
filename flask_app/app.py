from flask import Flask, Response, jsonify, request, abort
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
from flask_sqlalchemy import SQLAlchemy
from instance.config import *

# def create_app(config_name):
app = Flask(__name__)
app.config.from_object('instance.config.DevelopmentConfig')
app.config.from_pyfile('../instance/config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
api = Api(app)

from flask_app.resources.get_faces import GetFaces
from flask_app.resources.get_data_by_class import GetPersonFacesForClass

api.add_resource(GetFaces, '/api/photo/get_faces')
api.add_resource(GetPersonFacesForClass, '/api/get_data_by_class/<int:group_id>')