import os

class Config(object):
    """Parent configuration class."""
    DEBUG = False
    CSRF_ENABLED = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:test@localhost/face_recognition_db'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:test@localhost/face_recognition_db_ruby'
    REDIS_URL = 'redis://localhost:6380'
    FACE_LOCATION = '/run/user/1000/gvfs/smb-share:server=192.168.108.210,share=shares/face_images/'
    QUEUES = ['default']

class DevelopmentConfig(Config):
    """Configurations for Development."""
    DEBUG = True

class TestingConfig(Config):
    """Configurations for Testing, with a separate test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/test_db'
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