from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model

class UpdatePersonDetails(Resource):
    def post(self):
        data = dict(request.get_json(force=True))
        if len(data) > 0:
            person_id = data["person_id"]
            person_name = data["person_name"]
            kid_id = data["kid_id"]

            person = db.session.query(Model.Person).filter_by(id=person_id).first()
            person.name = person_name
            person.kid_id = kid_id
            db.session.commit()

            return jsonify({"status": 200, "message": str(person_id) + " is updated with person name as " + person_name + " and kid id as " + str(kid_id)})
        else:
            return jsonify({"status": 406, "message": "Method Not Allowed with NULL data."})


        # parse = reqparse.RequestParser()
        # parse.add_argument('person_id', type = int)
        # parse.add_argument('person_name', type = str)
        # parse.add_argument('kid_id', type = int)
