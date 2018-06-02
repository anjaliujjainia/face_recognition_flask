from flask_app.app import app, db
from sklearn.neural_network import MLPClassifier
import numpy as np
from datetime import datetime as dt
from flask_app import Model
import pdb

# mlp_classifier_pkl_file = app.config['PKL_FILE']
mlp_classifier_pkl_file = 'classifier/mlp_classifier.pkl'


def train():
	mlp_classifier_model_pkl = None
	try:
		# open pickle of already existing model
		mlp_classifier_model_pkl = open(mlp_classifier_pkl_file, 'rb')
	except FileNotFoundError as err:
		print(err)
	
	# get all faces
	all_faces = db.session.query(Model.Face).all()

	known_faces = {}
	unknown_faces = {}

	training_faces_encoding = []
	training_faces_id = []
	training_person_id = []

	unknown_faces_id = []

	if mlp_classifier_model_pkl:
		clf = pickle.load(mlp_classifier_model_pkl)
		print("Loaded CLF Model :: ", clf)
	else:
		clf = MLPClassifier(solver='adam',alpha=1e-5,random_state=1,max_iter=1000)
		print("Created New CLF Model :: ", clf)
		new_model = True


	for face in all_faces:
		face_id = face.id
		face_encoding = np.frombuffer(bytes.fromhex(face.encoding))
		face_person = face.person

		if(face.person_label_is_inferred == True):
			# we can use them for training
			training_faces_id.append(face_id)
			known_faces[face_id] = {}
			known_faces[face_id]['encoding'] = face_encoding
			known_faces[face_id]['person'] = face_person
			training_faces_encoding.append(face_encoding)
			training_person_id.append(face_person)
		else:
			unknown_faces_id.append()
			unknown_faces[face_id] = {}
			unknown_faces[face_id]['encoding'] = face_encoding
			unknown_faces[face_id]['person'] = face_person

	if new_model:
		face_id = unknown_faces_id[0]
		training_faces_encoding.append(unknown_faces[face_id]['encoding'])
		training_person_id.append(unknown_faces[face_id]['person'])

		face_encodings_known = np.array([f for f in training_faces_encoding])
		person_ids_known = np.array([f for f in training_person_id])
		pdb.set_trace()
		clf.fit(face_encodings_known, person_ids_known)


	for face_id in unknown_faces_id:
		# if face is predicted
		encoding = unknown_faces[face_id]['encoding']
		person = unknown_faces[face_id]['person']

		pred_person = clf.predict(encoding)[0] 
		probs = np.max(clf.predict_proba(encoding), 1)[0] 
		pdb.set_trace()
		if probs > 0.7:
			face = db.session.query(Model.Face).filter_by(id=face_id).first()
			face.person = pred_person
			face.person_label_is_inferred = True
			db.session.commit()
		else:
			# add it to training data and train the model
			training_faces_encoding.append(encoding)
			training_person_id.append(person)

			face_encodings_known = np.array([f for f in training_faces_encoding])
			person_ids_known = np.array([f for f in training_person_id])
			pdb.set_trace()
			clf.fit(face_encodings_known, person_ids_known)

	pickle.dump(clf, mlp_classifier_model_pkl)
	mlp_classifier_model_pkl.close()


if __name__ == "__main__":
	res=train()