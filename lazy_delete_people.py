#!/usr/bin/python
 
import psycopg2
from instance import config
import pdb
from flask_app.app import app

def delete_part():
    """ delete part by part id """
    conn = None
    rows_deleted = 0
    try:
        # connect to the PostgreSQL database
        database = app.config['SQLALCHEMY_DATABASE_URI']
        conn = psycopg2.connect(database)
        # create a new cursor
        cur = conn.cursor()
        pdb.set_trace()
        cur.execute("DELETE FROM person WHERE lazy_delete=TRUE")
        # get the number of updated rows
        rows_deleted = cur.rowcount
        # Commit the changes to the database
        conn.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return rows_deleted

if __name__ == '__main__':
    deleted_rows = delete_part()
    print('The number of deleted rows: ', deleted_rows)