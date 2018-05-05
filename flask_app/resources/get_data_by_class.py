from flask import request
from flask_restful import Resource, reqparse
from flask_app.Model import *

class GetPersonFacesForClass(Resource):
    # in agrs a group_id is given
    def get(self, group_id):
        personObj = db.session.query(Person).filter_by(group_id=group_id).all()
        faces = {}
        faces[group_id] = {}
        pdb.set_trace()
        # faces[group_id][personObj.id] = {}
        return jsonify({"group_id": group_id})
