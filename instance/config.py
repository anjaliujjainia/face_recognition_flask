import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import pdb

class Config(object):
    """Parent configuration class."""
    DEBUG = False
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    REDIS_URL = os.environ.get("REDIS_URL")
    FACE_LOCATION = os.environ.get("FACE_LOCATION")
    QUEUES = ['default']
    HOST = os.environ.get("HOST")
    PORT = os.environ.get("PORT")

class DevelopmentConfig(Config):
    """Configurations for Development."""
    DEBUG = True

class TestingConfig(Config):
    """Configurations for Testing, with a separate test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_TEST")
    DEBUG = True

class StagingConfig(Config):
    """Configurations for Staging."""
    DEBUG = True

class ProductionConfig(Config):
    """Configurations for Production."""
    DEBUG = False
    TESTING = False

app_config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
}