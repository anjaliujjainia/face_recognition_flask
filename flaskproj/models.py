from datetime import datetime
from hashlib import *

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_hash = db.Column(db.String(512), unique=True)
    image_path = db.Column(db.String(64))
    added_on = db.Column(db.DateTime, default=datetime.now)
    captions = db.Column(db.String(512))


    def __init__(self, image_hash, image_path, added_on, captions):
        self.image_path =  image_path
        self.image_hash = _generate_md5()
        self.added_on = added_on
        self.captions = captions

    def _generate_md5(self):
        hash_md5 = hashlib.md5()
        with open(self.image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class Face(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    # face_id = db.Column(db.String(64))
    photo = db.Column(db.ForeignKey('photo.id'))
    # face_embedding = db.Column(ARRAY(db.Float))
    encoding = db.Column(ARRAY(db.Float))
    person = db.Column(db.Integer, db.ForeignKey('person.id'))
    image_path = db.Column(db.String(64))
    is_labeled = db.Column(db.Boolean)

    location_top = db.Column(db.Integer)
    location_bottom = db.Column(db.Integer)
    location_left = db.Column(db.Integer)
    location_right = db.Column(db.Integer)

    def __init__(self, f_uuid, photo, encoding, person, location_top, location_bottom, location_left, location_right, is_labeled=False):
        self.id = f_uuid
        self.photo = photo_id
        self.encoding = encoding
        self.person = person
        self.image_path = f_uuid

        self.location_top = location_top
        self.location_bottom = location_bottom
        self.location_left = location_left
        self.location_right = location_right

        self.is_labeled = is_labeled
    
    def __repr__(self):
        return '<Face %r>' % self.id

# was cluster
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    mean_encoding = db.Column(ARRAY(db.Float))
    cluster_id = db.Column(db.Integer)

    def __init__(self, mean_encoding, name, cluster_id):
        self.name = name
        self.mean_encoding = mean_encoding
        self.cluster_id = cluster_id

    
    def __repr__(self):
        return '<Person %r>' % self.id

    # to do 
    def __update_average_face_encoding(self):
        encodings = []
        faces = self.faces.all()
        for face in faces:
            r = base64.b64decode(face.encoding)
            encoding = np.frombuffer(r,dtype=np.float64)
            encodings.append(encoding)
        mean_encoding = np.array(encodings).mean(axis=0)
        # self.mean_face_encoding = base64.encodebytes(mean_encoding.tostring())
        self.mean_face_encoding = list(mean_encoding)

# to do many to many field
class AlbumUser(db.Model):
    album_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), blank=True,null=True,max_length=512)
    timestamp = db.Column(db.DateTime, unique=True, db_index=True)
    created_on = db.Column(db.DateTime, auto_now=True,db_index=True)
    # photos = db.relationship('Photo', ) # many to many
