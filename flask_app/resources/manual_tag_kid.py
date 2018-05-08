from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db


#  '/api/manual_tag_kid'
class ManualTagKid(Resource):
    def post(self):
        data = dict(request.get_json(force=True))
        if len(data) > 0:
            photo_id = data["photo_id"]
            kid_id = data["kid_id"]
            # person_name = data["person_name"]
            # kid_name = data["kid_name"]

            person = db.session.query(Model.Person).filter_by(kid_id=kid_id).first()
            get_face_id = person.default_face
            face = db.session.query(Model.Face).filter_by(id=get_face_id).first()
            face_img_path = face.image_path
            face_encoding = face.encoding

            # since no faced was mentioned of the picture
            top, bottom, left, right = [-1, -1, -1, -1]
            faceId = str(uuid.uuid4())
            faceObj = Model.Face(faceId, photo_id, face_encoding, person.id, face_img_path, top, bottom, left, right)
            db.session.add(faceObj)
            db.session.commit()

            return jsonify({"status": 200, "message": str(person_name) + " added to photo"})
        else:
            return jsonify({"status": 406, "message": "Method Not Allowed with NULL data."})
