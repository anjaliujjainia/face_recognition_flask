class GetPersonFacesForClass(Resource):
    # in agrs a group_id is given
    def get(self, group_id):
        personObj = db.session.query(Person).filter_by(group_id=group_id).all()
        pdb.set_trace()
        faces = {}
        faces[group_id] = {}
        # faces[group_id][personObj.id] = {}
        return jsonify({"group_id": group_id})
