# -*- coding: utf-8 -*-
"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()
os_env = os.environ

class Config(object):
    """Base configuration."""

    SECRET_KEY = os_env.get('DRIBDAT_SECRET', 'A-big-scary-Secret-goes-HERE.')

    # Application options
    DRIBDAT_CLOCK = os_env.get('DRIBDAT_CLOCK', 'down')
    DRIBDAT_APIKEY = os_env.get('DRIBDAT_APIKEY', None)
    DRIBDAT_NOT_REGISTER = os_env.get('DRIBDAT_NOT_REGISTER', False)

    # TODO: per-event
    DRIBDAT_CERT_PATH = os_env.get('DRIBDAT_CERT_PATH', None)

    # Single sign-on support
    OAUTH_ID = os_env.get('OAUTH_ID', None)
    OAUTH_TYPE = os_env.get('OAUTH_TYPE', '').lower()
    OAUTH_SECRET = os_env.get('OAUTH_SECRET', None)
    OAUTH_DOMAIN = os_env.get('OAUTH_DOMAIN', None)

    # Application settings
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'null'
    CACHE_NO_NULL_WARNING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Server settings
    SERVER_NAME = os_env.get('SERVER_URL', '127.0.0.1:5000')
    SERVER_SSL = os_env.get('SERVER_SSL', None)
    TIME_ZONE = os_env.get('TIME_ZONE', 'UTC')
    MAX_CONTENT_LENGTH = os_env.get('MAX_CONTENT_LENGTH', 1 * 1024 * 1024)

    # Configure web analytics providers
    ANALYTICS_HREF = os_env.get('ANALYTICS_HREF', None)
    ANALYTICS_SIMPLE = os_env.get('ANALYTICS_SIMPLE', None)
    ANALYTICS_GOOGLE = os_env.get('ANALYTICS_GOOGLE', None)
    ANALYTICS_FATHOM = os_env.get('ANALYTICS_FATHOM', None)
    ANALYTICS_FATHOM_SITE = os_env.get('ANALYTICS_FATHOM_SITE', None)

    # S3 uploads support
    S3_KEY = os_env.get('S3_KEY', None)
    S3_SECRET = os_env.get('S3_SECRET', None)
    S3_REGION = os_env.get('S3_REGION', 'eu-west-1')
    S3_BUCKET = os_env.get('S3_BUCKET', None)
    S3_FOLDER = os_env.get('S3_FOLDER', '')
    S3_HTTPS = os_env.get('S3_HTTPS', None)


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    CACHE_TYPE = os_env.get('DRIBDAT_CACHE_TYPE', 'simple')
    CACHE_MEMCACHED_SERVERS = os_env.get('MEMCACHED_SERVERS', '')
    CACHE_MEMCACHED_USERNAME = os_env.get('MEMCACHED_USERNAME', '')
    CACHE_MEMCACHED_PASSWORD = os_env.get('MEMCACHED_PASSWORD', '')
    SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', 'postgresql://localhost/example')
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    DB_NAME = 'dev.db'
    # Put the db file in project root
    DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH)
    DEBUG_TB_ENABLED = True
    ASSETS_DEBUG = True  # Don't bundle/minify static assets
    WTF_CSRF_ENABLED = False  # Allows form testing


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SERVER_NAME = 'localhost'
    # Pytest complains, but not sure how to fully change server name
    # SERVER_NAME = 'localhost.localdomain'
    WTF_CSRF_ENABLED = False  # Allows form testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False
