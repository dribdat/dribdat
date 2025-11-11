# -*- coding: utf-8 -*-
"""Application configuration."""

# Documentation: https://dribdat.cc/deploy.html#features

import os
from dotenv import load_dotenv
from json import loads
from .utils import strtobool

load_dotenv()
os_env = os.environ


class Config(object):
    """Base configuration."""

    SECRET_KEY = os_env.get("DRIBDAT_SECRET", "A-big-scary-Secret-goes-HERE.")
    SECRET_API = os_env.get("DRIBDAT_APIKEY", None)

    # Customization options
    DRIBDAT_CLOCK = os_env.get("DRIBDAT_CLOCK", "down")
    DRIBDAT_STYLE = os_env.get("DRIBDAT_STYLE", "")
    DRIBDAT_THEME = os_env.get("DRIBDAT_THEME", "brite")
    DRIBDAT_STAGE = os_env.get("DRIBDAT_STAGE", "")
    BACKBOARD_URL = os_env.get("BACKBOARD_URL", None)

    # Application options
    DRIBDAT_NOT_REGISTER = os_env.get("DRIBDAT_NOT_REGISTER", "False")
    DRIBDAT_NOT_REGISTER = bool(strtobool(DRIBDAT_NOT_REGISTER))
    DRIBDAT_USER_APPROVE = os_env.get("DRIBDAT_USER_APPROVE", "False")
    DRIBDAT_USER_APPROVE = bool(strtobool(DRIBDAT_USER_APPROVE))
    DRIBDAT_ALLOW_LOGINS = os_env.get("DRIBDAT_ALLOW_LOGINS", "True")
    DRIBDAT_ALLOW_LOGINS = bool(strtobool(DRIBDAT_ALLOW_LOGINS))
    DRIBDAT_ALLOW_EVENTS = os_env.get("DRIBDAT_ALLOW_EVENTS", "False")
    DRIBDAT_ALLOW_EVENTS = bool(strtobool(DRIBDAT_ALLOW_EVENTS))
    DRIBDAT_SOCIAL_LINKS = os_env.get("DRIBDAT_SOCIAL_LINKS", "True")
    DRIBDAT_SOCIAL_LINKS = bool(strtobool(DRIBDAT_SOCIAL_LINKS))

    # Single sign-on support
    OAUTH_TYPE = os_env.get("OAUTH_TYPE", "").lower()
    OAUTH_ID = os_env.get("OAUTH_ID", None)
    OAUTH_SECRET = os_env.get("OAUTH_SECRET", None)
    OAUTH_DOMAIN = os_env.get("OAUTH_DOMAIN", None)
    OAUTH_SCOPE = os_env.get("OAUTH_SCOPE", None)
    OAUTH_USERINFO = os_env.get("OAUTH_USERINFO", None)
    OAUTH_TOKEN_URL = os_env.get("OAUTH_TOKEN_URL", None)
    OAUTH_AUTH_URL = os_env.get("OAUTH_AUTH_URL", None)
    OAUTH_LOGO = os_env.get("OAUTH_LOGO", None)

    # (Optional) Go directly to external login screen
    OAUTH_SKIP_LOGIN = bool(strtobool(os_env.get("OAUTH_SKIP_LOGIN", "False")))
    OAUTH_LINK_REGISTER = os_env.get("OAUTH_LINK_REGISTER", None)
    OAUTH_HELP_REGISTER = os_env.get("OAUTH_HELP_REGISTER", None)

    # Mail service support
    MAIL_PORT = os_env.get("MAIL_PORT", 25)
    MAIL_SERVER = os_env.get("MAIL_SERVER", None)
    MAIL_USERNAME = os_env.get("MAIL_USERNAME", None)
    MAIL_PASSWORD = os_env.get("MAIL_PASSWORD", None)
    MAIL_DEFAULT_SENDER = os_env.get("MAIL_DEFAULT_SENDER", None)
    MAIL_USE_TLS = bool(strtobool(os_env.get("MAIL_USE_TLS", "False")))
    MAIL_USE_SSL = bool(strtobool(os_env.get("MAIL_USE_SSL", "False")))
    MAIL_NOTIFY_ADMIN = os_env.get("MAIL_NOTIFY_ADMIN", None)

    # Application settings
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = "SimpleCache"
    CACHE_NO_NULL_WARNING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Server settings
    SERVER_NAME = os_env.get(
        "SERVER_URL", os_env.get("SERVER_NAME", "localhost.localdomain:5000")
    )
    SERVER_SSL = bool(strtobool(os_env.get("SERVER_SSL", "False")))
    SERVER_CORS = bool(strtobool(os_env.get("SERVER_CORS", "True")))
    SERVER_PROXY = bool(strtobool(os_env.get("SERVER_PROXY", "False")))
    CSP_DIRECTIVES = os_env.get(
        "CSP_DIRECTIVES", "default-src * 'unsafe-inline' 'unsafe-eval' data:"
    )
    TIME_ZONE = os_env.get("TIME_ZONE", "UTC")
    MAX_CONTENT_LENGTH = int(os_env.get("MAX_CONTENT_LENGTH", 1 * 1024 * 1024))

    # Configure an external LLM API
    LLM_MODEL = os_env.get("LLM_MODEL", "local-model")  # e.g. gpt-3.5-turbo
    LLM_TITLE = LLM_MODEL.upper().replace("_", " ").split("/")[-1]
    LLM_API_KEY = os_env.get("LLM_API_KEY", "")
    LLM_BASE_URL = os_env.get("LLM_BASE_URL", "")

    # Configure web analytics providers
    ANALYTICS_HREF = os_env.get("ANALYTICS_HREF", None)
    ANALYTICS_SIMPLE = os_env.get("ANALYTICS_SIMPLE", None)
    ANALYTICS_GOOGLE = os_env.get("ANALYTICS_GOOGLE", None)
    ANALYTICS_FATHOM = os_env.get("ANALYTICS_FATHOM", None)

    # S3 uploads support
    S3_KEY = os_env.get("S3_KEY", None)
    S3_SECRET = os_env.get("S3_SECRET", None)
    S3_REGION = os_env.get("S3_REGION", "eu-west-1")
    S3_BUCKET = os_env.get("S3_BUCKET", None)
    S3_FOLDER = os_env.get("S3_FOLDER", "")
    S3_HTTPS = os_env.get("S3_HTTPS", None)
    S3_ENDPOINT = os_env.get("S3_ENDPOINT", None)

    # Default settings for AWS S3 integrity checks (see boto3 #4392)
    if not os_env.get("AWS_REQUEST_CHECKSUM_CALCULATION", None):
        os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "WHEN_REQUIRED"
        os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "WHEN_REQUIRED"

    # Recaptcha support
    RECAPTCHA_PUBLIC_KEY = os_env.get("RECAPTCHA_PUBLIC_KEY", None)
    RECAPTCHA_PRIVATE_KEY = os_env.get("RECAPTCHA_PRIVATE_KEY", None)
    RECAPTCHA_PARAMETERS = os_env.get("RECAPTCHA_PARAMETERS", None)
    RECAPTCHA_HTML = os_env.get("RECAPTCHA_HTML", None)
    RECAPTCHA_DATA_ATTRS = loads(os_env.get("RECAPTCHA_DATA_ATTRS", {}))
    RECAPTCHA_SCRIPT = os_env.get("RECAPTCHA_SCRIPT", None)
    RECAPTCHA_DIV_CLASS = os_env.get("RECAPTCHA_DIV_CLASS", None)
    RECAPTCHA_VERIFY_SERVER = os_env.get("RECAPTCHA_VERIFY_SERVER", None)


class ProdConfig(Config):
    """Production configuration."""

    ENV = "prod"
    DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    PREFERRED_URL_SCHEME = "https"  # For generating external URLs
    CACHE_TYPE = os_env.get("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL = os_env.get("CACHE_REDIS_URL", "")
    if CACHE_REDIS_URL:
        CACHE_TYPE = "RedisCache"
    CACHE_MEMCACHED_SERVERS = os_env.get("MEMCACHED_SERVERS", "")
    CACHE_MEMCACHED_USERNAME = os_env.get("MEMCACHED_USERNAME", "")
    CACHE_MEMCACHED_PASSWORD = os_env.get("MEMCACHED_PASSWORD", "")
    if CACHE_MEMCACHED_SERVERS:
        CACHE_TYPE = "MemcachedCache"
    CACHE_DEFAULT_TIMEOUT = int(os_env.get("CACHE_DEFAULT_TIMEOUT", "300"))
    DB_PATH = os.path.join(Config.PROJECT_ROOT, "dribdat.db")
    SQLALCHEMY_DATABASE_URI = os_env.get(
        "DATABASE_URL", "sqlite:///{0}".format(DB_PATH)
    )
    # Compatibility with old-style postgres config
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
        "postgres:/", "postgresql:/"
    )


class DevConfig(Config):
    """Development configuration."""

    ENV = "dev"
    DEBUG = True
    SERVER_NAME = "127.0.0.1:5000"
    # Put the db file in project root
    DB_PATH = os.path.join(Config.PROJECT_ROOT, "dev.db")
    SQLALCHEMY_DATABASE_URI = "sqlite:///{0}".format(DB_PATH)
    CACHE_TYPE = "NullCache"  # Do not cache
    DEBUG_TB_ENABLED = True  # Enable the Debug Toolbar
    ASSETS_DEBUG = True  # Don't bundle/minify static assets
    WTF_CSRF_ENABLED = False  # Allows form testing


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SERVER_NAME = "localhost"
    MAIL_DEFAULT_SENDER = "test@dribdat.cc"
    # Pytest complains, but not sure how to fully change server name
    # SERVER_NAME = 'localhost.localdomain' #results in 404 errors
    WTF_CSRF_ENABLED = False  # Allows form testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    DRIBDAT_ALLOW_EVENTS = True  # Allows anyone to create an event
