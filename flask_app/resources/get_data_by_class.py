from flask import request, jsonify
from flask_restful import Resource, reqparse
from flask_app import Model
# from flask_app.Model import *
from flask_app.app import db
import pdb

class GetPersonFacesForClass(Resource):
    # in agrs a group_id is given
    def get(self, group_id):
        personObj = db.session.query(Model.Person).filter_by(group_id=group_id).all()
        # pdb.set_trace()
        faces = {}
        faces[group_id] = {}
        for person in personObj:
            person_id = person.id

            # ####### PERSON ID DICT ############
            faces[group_id][person.id] = {}
            faces[group_id][person.id]["person_face_image"] = {}
            faces[group_id][person.id]["person_images_ids"] = []
            # ######## END ###############

            # getting persons default face
            default_face_id = person.default_face
            # get that face obj for its id and url
            faceObj = db.session.query(Model.Face).filter_by(id=default_face_id).first()
            faces[group_id][person.id]["person_face_image"]["face_image_id"] = faceObj.id 
            faces[group_id][person.id]["person_face_image"]["face_image_url"] = faceObj.image_path

            # getting all the images of that person 
            facesObj = db.session.query(Model.Face).filter_by(person=person_id).all()
            all_images = []
            for each_face in facesObj:
                photo_id_of_face = each_face.photo
                photoObj = db.session.query(Model.Photo).filter_by(id=photo_id_of_face).first()
                all_images.append(photoObj.ruby_id)

            faces[group_id][person.id]["person_images_ids"] = all_images
            # pdb.set_trace()
        # faces[group_id][personObj.id] = {}
        return jsonify({"faces": faces})
