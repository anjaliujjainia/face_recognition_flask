from flask import request, jsonify
from flask_restful import Resource
import pdb

class PhotoDetailResponse(Resource):
	def post(self):
		data = dict(request.get_json(force=True))
		# print(data)
		return jsonify({"status": 200, "message":"Data recieved!"})