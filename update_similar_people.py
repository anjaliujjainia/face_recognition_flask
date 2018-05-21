#!/usr/bin/python
 
import psycopg2
from instance import config
import pdb
from flask_app.app import app
import numpy as np
import face_recognition

# Update Mean Encoding
def update_mean_encoding(myself, face_encoding):
    encodings = []
    encodings.append(myself)
    encodings.append(face_encoding)
    mean_encoding = np.array(encodings).mean(axis=0)
    return str(list(mean_encoding)).replace("[", "{").replace("]", "}")

def main():
    """ Update person if two person are same """
    conn = None
    try:
        # connect to the PostgreSQL database
        database = app.config['SQLALCHEMY_DATABASE_URI']
        conn = psycopg2.connect(database)
        # create a new cursor
        cur = conn.cursor()
        # get all persons from table
        cur.execute('SELECT * FROM person')
        persons = cur.fetchall()
        if len(persons) > 1:
            knownFaceEncodings = [_[2] for _ in persons]
            knownFaceIds = [_[0] for _ in persons]
            for i, encoding in enumerate(knownFaceEncodings):
                for j in range(i, len(knownFaceEncodings)):
                    face_distance = face_recognition.face_distance([np.array(knownFaceEncodings[j])],
                    # Same Person
                    if face_distance < 0.6:
                        mean_encoding = update_mean_encoding(encoding, knownFaceEncodings[j])
                        # Update database
                        cur.execute("UPDATE person SET mean_encoding='{0}' WHERE id={1}".format(mean_encoding, knownFaceIds[i]))
                        cur.execute("UPDATE person SET lazy_delete={0} WHERE id={1}".format("TRUE", knownFaceIds[j]))
                        cur.execute("UPDATE face SET person={0} WHERE person={1}".format(knownFaceIds[i], knownFaceIds[j]))
                        # Commit Changes
                        conn.commit()
                        print("Person with id: {0} is converted to person with id: {1} and {2} rows in face table are affected.".format(knownFaceIds[j], knownFaceIds[i]))
                        break
        
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return rows_deleted

if __name__ == '__main__':
    main()