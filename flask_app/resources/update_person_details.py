from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model
from flask_app.app import db


#  '/api/update_person_details'
class UpdatePersonDetails(Resource):
    def post(self):
        data = dict(request.get_json(force=True))
        msg = ''
        if len(data) > 0:
            person_id = data["person_id"]
            person_name = data["person_name"]
            kid_id = data["kid_id"]
            # check if any person with the same kid_id exist
            # original person
            o_person = db.session.query(Model.Person).filter_by(kid_id=kid_id).first()
            o_person_id = o_person.id
            person = db.session.query(Model.Person).filter_by(id=person_id).first()
            
            if o_person and o_person_id != person_id:
                msg =  person_name + " with the kid_id :: " + str(kid_id) +" already exist. Updating :: " + o_person_id
                o_person.name = person_name
                # get all the faces of the person_id
                faces = db.session.query(Model.Face).filter_by(person=person_id).all()
                for face in faces:
                    face.person = o_person_id
                person.lazy_delete = True
            else:
                msg = str(person_id) + " is updated with person name as " + person_name + " and kid id as " + str(kid_id)
                person.name = person_name
                person.kid_id = kid_id
            print(msg)
            db.session.commit()
            return jsonify({"status": 200, "message": msg})
        else:
            return jsonify({"status": 406, "message": "Method Not Allowed with NULL data."})