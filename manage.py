import os
from flask_script import Server, Manager # class for handling a set of commands
from flask_migrate import Migrate, MigrateCommand
# from app import db, create_app
from flask_app import Model
from flask_app.app import app, db
from rq import Connection, Worker
import redis

# app = create_app(ocnfig_name='development')
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(host=app.config['HOST'], port=app.config['PORT']))

@manager.command
def runworker():
    redis_url = app.config['REDIS_URL']
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(app.config['QUEUES'])
        worker.work()


if __name__ == '__main__':
    manager.run()