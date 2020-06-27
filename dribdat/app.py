# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS

from dribdat import commands, public, user, admin
from dribdat.assets import assets
from dribdat.extensions import (
    hashing,
    cache,
    db,
    login_manager,
    migrate,
)
from dribdat.settings import ProdConfig
from dribdat.utils import timesince
from flask_misaka import Misaka
from flask_talisman import Talisman
from flask_dance.contrib.slack import make_slack_blueprint, slack

def init_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config['CORS_HEADERS'] = 'Content-Type'

    register_extensions(app)
    register_blueprints(app)
    register_oauthhandlers(app)
    register_errorhandlers(app)
    register_filters(app)
    register_loggers(app)
    register_shellcontext(app)
    register_commands(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    assets.init_app(app)
    hashing.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    if 'SERVER_SSL' in app.config and app.config['SERVER_SSL']:
        Talisman(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(public.auth.blueprint)
    app.register_blueprint(public.api.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(admin.views.blueprint)
    return None

def register_oauthhandlers(app):
    if "DRIBDAT_SLACK_ID" in app.config:
        blueprint = make_slack_blueprint(
            client_id=app.config["DRIBDAT_SLACK_ID"],
            client_secret=app.config["DRIBDAT_SLACK_SECRET"],
            redirect_to="public.home",
            login_url="/slack_login",
            authorized_url=None,
            session_class=None,
            storage=None,
            scope="identify,chat:write:bot,identity.basic,identity.email"
        )
        app.register_blueprint(blueprint, url_prefix="/oauth")

def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def register_filters(app):
    Misaka(app, autolink=True, fenced_code=True, strikethrough=True, tables=True)
    @app.template_filter()
    def since_date(value):
        return timesince(value)
    @app.template_filter()
    def until_date(value):
        return timesince(value, default="now!", until=True)
    @app.template_filter()
    def format_date(value, format='%d.%m.%Y'):
        return value.strftime(format)
    @app.template_filter()
    def format_datetime(value, format='%H:%M %d.%m.%Y'):
        return value.strftime(format)


def register_loggers(app):
    # if os.environ.get('HEROKU') is not None:
        # app.logger.info('hello Heroku!')
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
