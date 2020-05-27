"""App configuration."""
from os import environ
import redis
from urllib.parse import urlparse


class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SECRET_KEY = environ.get('SECRET_KEY')
    FLASK_APP = environ.get('FLASK_APP')
    FLASK_ENV = environ.get('FLASK_ENV')

    # Flask-Session
    SESSION_TYPE = environ.get('SESSION_TYPE')
    REDISCLOUD_URL = environ.get('REDISCLOUD_URL')

    url = urlparse(REDISCLOUD_URL)
    SESSION_REDIS = redis.Redis(host=url.hostname, port=url.port, password=url.password)

    #SESSION_REDIS = redis.from_url(environ.get('REDISCLOUD_URL'))


