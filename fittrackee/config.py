import os
from pathlib import Path

from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from flask import current_app
from sqlalchemy.pool import NullPool

if os.getenv('APP_SETTINGS') == 'fittrackee.config.TestingConfig':
    broker = StubBroker
else:
    broker = RedisBroker


class BaseConfig:
    """Base configuration"""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 13
    TOKEN_EXPIRATION_DAYS = 30
    TOKEN_EXPIRATION_SECONDS = 0
    PASSWORD_TOKEN_EXPIRATION_SECONDS = 3600
    UPLOAD_FOLDER = os.path.join(
        os.getenv('UPLOAD_FOLDER', current_app.root_path), 'uploads'
    )
    PICTURE_ALLOWED_EXTENSIONS = {'jpg', 'png', 'gif'}
    WORKOUT_ALLOWED_EXTENSIONS = {'gpx', 'zip'}
    TEMPLATES_FOLDER = os.path.join(current_app.root_path, 'emails/templates')
    UI_URL = os.environ['UI_URL']
    EMAIL_URL = os.environ.get('EMAIL_URL')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
    DRAMATIQ_BROKER = broker
    TILE_SERVER = {
        'URL': os.environ.get(
            'TILE_SERVER_URL',
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        ),
        'ATTRIBUTION': os.environ.get(
            'MAP_ATTRIBUTION',
            '&copy; <a href="http://www.openstreetmap.org/copyright" '
            'target="_blank" rel="noopener noreferrer">OpenStreetMap</a>'
            ' contributors',
        ),
    }
    VERSION = (Path(f'{current_app.root_path}/VERSION')).read_text().strip()
    # ActivityPub
    AP_DOMAIN = UI_URL.replace('https://', '')


class DevelopmentConfig(BaseConfig):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = 'development key'
    USERNAME = 'admin'
    PASSWORD = 'default'
    BCRYPT_LOG_ROUNDS = 4
    DRAMATIQ_BROKER_URL = os.getenv('REDIS_URL', 'redis://')


class TestingConfig(BaseConfig):
    """Testing configuration"""

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_TEST_URL')
    SECRET_KEY = 'test key'
    USERNAME = 'admin'
    PASSWORD = 'default'
    BCRYPT_LOG_ROUNDS = 4
    TOKEN_EXPIRATION_DAYS = 0
    TOKEN_EXPIRATION_SECONDS = 3
    PASSWORD_TOKEN_EXPIRATION_SECONDS = 3
    UPLOAD_FOLDER = '/tmp/fitTrackee/uploads'


class ProductionConfig(BaseConfig):
    """Production configuration"""

    DEBUG = False
    # https://docs.sqlalchemy.org/en/13/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork  # noqa
    SQLALCHEMY_ENGINE_OPTIONS = (
        {'poolclass': NullPool}
        if os.getenv('DATABASE_DISABLE_POOLING', False)
        else {}
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = os.getenv('APP_SECRET_KEY')
    DRAMATIQ_BROKER_URL = os.getenv('REDIS_URL', 'redis://')
