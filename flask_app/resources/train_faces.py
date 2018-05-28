'''
get all the false face_is_labelled faces
pickle.dump(data_to_dump, file_to_dump_to)
data_dumped = pickle.load(file_to_dump_to)

'''
from flask_app.app import app, db
from sklearn.neural_network import MLPClassifier
import numpy as np
from datetime import datetime as dt
from flask_app import Model
import pdb


# mlp_classifier_pkl_file = app.config['PKL_FILE']
mlp_classifier_pkl_file = 'mlp_classifier.pkl'

def train_faces():
	# faces which arent labelled/inferred yet.
	false_faces = db.session.query(Model.Face).filter_by(face_is_labeled=False).all()
	unknown_encodings = []
	unknown_names = [] 

	mlp_classifier_model_pkl = open(mlp_classifier_pkl_file, 'rb')
	if mlp_classifier_model_pkl:
		clf_model = pickle.load(mlp_classifier_model_pkl)
		print("Loaded CLF Model :: ", clf_model)
	else:
		clf_model = MLPClassifier(solver='adam',alpha=1e-5,random_state=1,max_iter=1000)
		print("Created Ne wCLF Model :: ", clf_model)


	# mlp_classifier_model_pkl = open(mlp_classifier_pkl_file, 'wb')
	# open pickle of already existing model
	
	for face in false_faces:
		unknown_encodings.append(face.encoding)
		p_id = face.person
		person = db.session.query(Model.Person).filter_by(id=p_id).first()
		person_name = person.name + str(p_id)
		unknown_names.append(person_name)
		'''
		for each unknown face, classify it using the model, 
		if none's probability is above 90%, then create a new class
		'''
		unknown_encodings_array = np.array([f for f in unknown_encodings])
		unknown_names_array = np.array([f for f in unknown_names])

		clf_model.fit(unknown_encodings_array, unknown_names_array)
	

	pickle.dump(clf_model, mlp_classifier_model_pkl)
	mlp_classifier_model_pkl.close()




if __name__ == "__main__":
    res=train_faces()