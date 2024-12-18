# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""

from flask import Flask, render_template
from flask_cors import CORS
from flask_mailman import Mail
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from micawber.providers import bootstrap_basic
from whitenoise import WhiteNoise
from urllib.parse import quote_plus
from dribdat import commands, public, admin
from dribdat.assets import assets  # noqa: I005
from dribdat.sso import get_auth_blueprint
from dribdat.extensions import (
    hashing,
    cache,
    db,
    login_manager,
    migrate,
)
from dribdat.settings import ProdConfig  # noqa: I005
from dribdat.utils import timesince, markdownit
from dribdat.onebox import make_oembedplus
from pytz import timezone


def init_app(config_object=ProdConfig):
    """Define an application factory.

    See: http://flask.pocoo.org/docs/patterns/appfactories/

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Set up cross-site access to the API
    if app.config['SERVER_CORS']:
        CORS(app, resources={r"/api/*": {"origins": "*"}})
        app.config['CORS_HEADERS'] = 'Content-Type'

    # Set up using an external proxy/static server
    if app.config['SERVER_PROXY']:
        app.wsgi_app = ProxyFix(app, x_for=1, x_proto=1, x_host=1)
    else:
        # Internally optimize static file hosting
        app.wsgi_app = WhiteNoise(app.wsgi_app, prefix='static/')
        for static in ('css', 'img', 'js', 'public'):
            app.wsgi_app.add_files('dribdat/static/' + static)

    register_extensions(app)
    register_blueprints(app)
    register_oauthhandlers(app)
    register_errorhandlers(app)
    register_filters(app)
    register_loggers(app)
    register_shellcontext(app)
    register_commands(app)
    register_caching(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    assets.init_app(app)
    hashing.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    init_mailman(app)
    init_talisman(app)
    return None


def init_mailman(app):
    """Initialize mailer support."""
    if 'MAIL_SERVER' in app.config and app.config['MAIL_SERVER']:
        if not app.config['MAIL_DEFAULT_SENDER']:
            app.logger.warn('MAIL_DEFAULT_SENDER is required to send email')
        else:
            mail = Mail()
            mail.init_app(app)


def init_talisman(app):
    """Initialize Talisman support."""
    if 'SERVER_SSL' in app.config and app.config['SERVER_SSL']:
        Talisman(app,
                 content_security_policy=app.config['CSP_DIRECTIVES'],
                 frame_options_allow_from='*')


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.api.blueprint)
    app.register_blueprint(public.auth.blueprint)
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(public.feeds.blueprint)
    app.register_blueprint(public.project.blueprint)
    app.register_blueprint(admin.views.blueprint)
    return None


def register_oauthhandlers(app):
    """Set up OAuth handlers based on configuration."""
    blueprint = get_auth_blueprint(app)
    if blueprint is not None:
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
        from dribdat.user.models import User
        return {
            'db': db,
            'User': User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def register_filters(app):
    """Register filters for templates."""
    #
    # Conversion of Markdown to HTML
    @app.template_filter()
    def markdown(value):
        return markdownit(value)

    #Misaka(app, autolink=True, fenced_code=True, strikethrough=True, tables=True)

    # Registration of handlers for micawber
    app.oembed_providers = bootstrap_basic()

    @app.template_filter()
    def onebox(value):
        return make_oembedplus(
            value, app.oembed_providers, maxwidth=600, maxheight=400
        )

    # Timezone helper
    app.tz = timezone(app.config['TIME_ZONE'] or 'UTC')

    # Lambda filters for safe image_url's
    app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u or '', ':/?&=')

    # Custom filters
    @app.template_filter()
    def since_date(value):
        return timesince(value)

    @app.template_filter()
    def until_date(value):
        return timesince(value, default="now!", until=True)

    @app.template_filter()
    def format_date(value, format='%d.%m.%Y'):
        if value is None: return ''
        return value.strftime(format)

    @app.template_filter()
    def format_datetime(value, format='%d.%m.%Y %H:%M'):
        if value is None: return ''
        return value.strftime(format)


def register_loggers(app):
    """Initialize and configure logging."""
    if 'DEBUG' in app.config and not app.config['DEBUG']:
        import logging
        stream_handler = logging.StreamHandler()
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)


def register_caching(app):
    """Prevent cached responses in debug."""
    if 'DEBUG' in app.config and app.config['DEBUG']:
        @app.after_request
        def after_request(response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
            response.headers["Expires"] = 0
            response.headers["Pragma"] = "no-cache"
            return response
