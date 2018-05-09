from flask import request, jsonify
from flask_restful import Resource, reqparse
# from flask_app.Model import Face, Person, Photo
from flask_app import Model
from flask_app.app import db, app


# Untag Person Manually (Arguments:- person_id, photo_id as post request)
class UntagPerson(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('photo_id', type = str) # argument for photo id
        parse.add_argument('person_id', type = str) # argument for person id
        args = parse.parse_args()

        if args['photo_id'] != "" and args['person_id'] != "":
            photo_id = int(args['photo_id'])
            person_id = int(args['person_id'])
            faces = db.session.query(Model.Face).filter_by(photo=photo_id).all() # Getting all faces with given photo id
            for face in faces:
                if face.person == person_id:
                    face.person = None # Removing person from photo when person == given person
                    db.session.commit()
                    return jsonify({ 'status': 200, 'message': 'Person with person id '+ str(person_id) + " is removed from photo" })
            
            return jsonify({ 'status': 404, 'message': 'Person with person id '+ str(person_id) + " not found in photo" })
        else:
            return jsonify({'status': 406, 'message': 'Please provide both photo id and person id'})