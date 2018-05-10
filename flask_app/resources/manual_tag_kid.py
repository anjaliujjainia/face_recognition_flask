from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db
import pdb
from uuid import uuid4

#  '/api/manual_tag_kid'
class ManualTagKid(Resource):
    def post(self):
        data = dict(request.get_json(force=True))
        if len(data) > 0:
            ruby_id = data["photo_id"]
            kid_id = data["kid_id"]
            # pdb.set_trace()
            # given ruby id and kid id, get the image and person
            photoObj = db.session.query(Model.Photo).filter_by(ruby_id=ruby_id).first()
            person = db.session.query(Model.Person).filter_by(kid_id=kid_id).first()
            
            get_face_id = person.default_face
            face = db.session.query(Model.Face).filter_by(id=get_face_id).first()
            face_img_path = face.image_path
            face_encoding = face.encoding

            # since no face is mentioned in the picture
            top, bottom, left, right = [-1, -1, -1, -1]
            faceId = str(uuid4())
            faceObj = Model.Face(faceId, photoObj.id, face_encoding, person.id, face_img_path, top, bottom, left, right, face_is_labeled=True)
            db.session.add(faceObj)
            db.session.commit()

            return jsonify({"status": 200, "message": str(person.name) + " added to photo"})
        else:
            return jsonify({"status": 406, "message": "Method Not Allowed with NULL data."})
