from datetime import datetime
from hashlib import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY

from __main__ import app
from flask_migrate import Migrate

import numpy as np

db = SQLAlchemy(app)
# migrate = Migrate(app, db) 


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_hash = db.Column(db.String(512), unique=True)
    image_path = db.Column(db.String(512))
    added_on = db.Column(db.DateTime, default=datetime.now)
    captions = db.Column(db.String(512))


    def __init__(self, image_path, image_hash, captions):
        self.image_path =  image_path
        self.image_hash = image_hash
        self.captions = captions

    def __repr__(self):
        return '<Photo %r>' % self.id

class Face(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    # face_id = db.Column(db.String(64))
    photo = db.Column(db.ForeignKey('photo.id'))
    # face_embedding = db.Column(ARRAY(db.Float))
    encoding = db.Column(ARRAY(db.Float))
    person = db.Column(db.Integer, db.ForeignKey('person.id'))
    person_is_labeled = db.Column(db.Boolean)
    image_path = db.Column(db.String(64))

    location_top = db.Column(db.Integer)
    location_bottom = db.Column(db.Integer)
    location_left = db.Column(db.Integer)
    location_right = db.Column(db.Integer)

    def __init__(self, f_uuid, photo_id, encoding, person, location_top, location_bottom, location_left, location_right, person_is_labeled = False):
        self.id = f_uuid
        self.photo = photo_id
        self.encoding = encoding
        self.person = person
        self.image_path = str(f_uuid) + '.jpg'

        self.location_top = location_top
        self.location_bottom = location_bottom
        self.location_left = location_left
        self.location_right = location_right
        self.person_is_labeled = person_is_labeled

    
    def __repr__(self):
        return '<Face %r>' % self.id

# was cluster
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    mean_encoding = db.Column(ARRAY(db.Float))
    cluster_id = db.Column(db.Integer)
    kid_id = db.Column(db.Integer)
    is_labeled = db.Column(db.Boolean)

    def __init__(self, mean_encoding, name, cluster_id=None, kid_id = None, is_labeled=False):
        self.name = name
        self.mean_encoding = mean_encoding
        self.cluster_id = cluster_id
        self.kid_id = kid_id
        self.is_labeled = is_labeled

    
    def __repr__(self):
        return '<Person %r>' % self.id

    # change function accorning to need
    def update_average_face_encoding(self, face_encoding):
        myself = self.mean_encoding
        encodings = []
        encodings.append(myself)
        encodings.append(face_encoding)
        mean_encoding = np.array(encodings).mean(axis=0)
        self.mean_encoding = list(mean_encoding)

# to do many to many field
class AlbumUser(db.Model):
    album_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, unique=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    # photos = db.relationship('Photo', ) # many to many
