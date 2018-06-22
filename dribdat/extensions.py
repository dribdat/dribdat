# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_hashing import Hashing
from flask_caching import Cache
from flask_login import LoginManager
from flask_oauth import OAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

hashing = Hashing()
login_manager = LoginManager()
login_oauth = OAuth()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
