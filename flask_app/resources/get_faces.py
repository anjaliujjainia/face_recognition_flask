import requests
import pdb
from rq import Queue
# from worker import conn
from . import task_save_faces
from rq import push_connection, pop_connection, Queue
from flask import Blueprint, render_template, request, jsonify, current_app, g, url_for
import redis
from flask_restful import Resource

# bp = Blueprint('main', __name__)

def get_redis_connection():
    redis_connection = getattr(g, '_redis_connection', None)
    if redis_connection is None:
        redis_url = current_app.config['REDIS_URL']
        redis_connection = g._redis_connection = redis.from_url(redis_url)
    return redis_connection

class GetFaces(Resource):
    def post(self):
        # task = request.form.get('task')
        task = dict(request.get_json(force=True))
        conn = get_redis_connection()
        q = Queue(connection=conn)
        if len(task) > 0:
            print("Printing task")
            print(task)
            print("===========Enqueuing task!===========")
            job = q.enqueue(task_save_faces.run, task, timeout=800)
            return jsonify({"status": 202, "message": "Accepted"})#, {'Location': url_for('job_status', job_id=job.get_id())}
        else:
            return jsonify({"status": 406, "message": "Please Provide Data!"})
    
    # @bp.route('/status/<job_id>')
    def job_status(job_id):
        q = Queue(connection = get_redis_connection())
        job = q.fetch_job(job_id)
        if job is None:
            response = {'status': 'unknown'}
        else:
            response = {
                'status': job.get_status(),
                'result': job.result,
            }
            if job.is_failed:
                response['message'] = job.exc_info.strip().split('\n')[-1]
        return jsonify(response)