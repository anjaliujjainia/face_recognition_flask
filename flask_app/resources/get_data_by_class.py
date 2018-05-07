from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model
# from flask_app.Model import *
from flask_app.app import db
import pdb

class GetPersonFacesForClass(Resource):
    # in agrs a group_id is given
    def get(self, group_id):
        pdb.set_trace()
        personObj = db.session.query(Model.Person).filter_by(group_id=group_id).all()
        faces = {}
        faces[group_id] = {}
        # faces[group_id][personObj.id] = {}
        return jsonify({"group_id": group_id})
