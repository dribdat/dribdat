# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""

from flask import Flask, render_template
from flask_cors import CORS
from flask_misaka import Misaka
from flask_mailman import Mail
from flask_talisman import Talisman
from flask_dance.contrib import (slack, azure, github)
from werkzeug.middleware.proxy_fix import ProxyFix
from micawber.providers import bootstrap_basic
from whitenoise import WhiteNoise
from pytz import timezone
from urllib.parse import quote_plus
from dribdat import commands, public, admin
from dribdat.assets import assets  # noqa: I005
from dribdat.extensions import (
    hashing,
    cache,
    db,
    login_manager,
    migrate,
)
from dribdat.settings import ProdConfig  # noqa: I005
from dribdat.utils import timesince
from dribdat.onebox import make_oembedplus


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
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(public.project.blueprint)
    app.register_blueprint(public.auth.blueprint)
    app.register_blueprint(public.api.blueprint)
    app.register_blueprint(admin.views.blueprint)
    return None


def register_oauthhandlers(app):
    """Set up OAuth handlers based on configuration."""
    # TODO: move to auth class
    blueprint = None
    if not app.config['OAUTH_TYPE']:
        return
    if app.config['OAUTH_TYPE'] == 'slack':
        blueprint = slack.make_slack_blueprint(
            client_id=app.config['OAUTH_ID'],
            client_secret=app.config['OAUTH_SECRET'],
            scope="identity.basic,identity.email",
            redirect_to="auth.slack_login",
            login_url="/login",
            # authorized_url=None,
            # session_class=None,
            # storage=None,
            subdomain=app.config['OAUTH_DOMAIN'],
        )
    elif app.config['OAUTH_TYPE'] == 'azure':
        blueprint = azure.make_azure_blueprint(
            client_id=app.config['OAUTH_ID'],
            client_secret=app.config['OAUTH_SECRET'],
            tenant=app.config['OAUTH_DOMAIN'],
            scope="profile email User.ReadBasic.All openid",
            redirect_to="auth.azure_login",
            login_url="/login",
        )
    elif app.config['OAUTH_TYPE'] == 'github':
        blueprint = github.make_github_blueprint(
            client_id=app.config['OAUTH_ID'],
            client_secret=app.config['OAUTH_SECRET'],
            # scope="user,read:user",
            redirect_to="auth.github_login",
            login_url="/login",
        )
    elif app.config['OAUTH_TYPE'] == 'oauth2':
        from flask_dance.consumer import OAuth2ConsumerBlueprint
        blueprint = OAuth2ConsumerBlueprint(
            "oauth2-provider", __name__,
            client_id=app.config['OAUTH_ID'],
            client_secret=app.config['OAUTH_SECRET'],
            base_url=app.config['OAUTH_BASE_URL'],
            token_url=app.config['OAUTH_TOKEN_URL'],
            authorization_url=app.config['OAUTH_AUTH_URL'],
            redirect_to="auth.oauth_login",
            login_url="/login",
        )
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
    Misaka(app, autolink=True, fenced_code=True,
           strikethrough=True, tables=True)

    # Registration of handlers for micawber
    app.oembed_providers = bootstrap_basic()

    @app.template_filter()
    def onebox(value):
        return make_oembedplus(
            value, app.oembed_providers, maxwidth=600, maxheight=400
        )

    # Timezone helper
    app.tz = timezone(app.config['TIME_ZONE'])

    # Lambda filters
    app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u, ':/?')

    # Custom filters
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
    def format_datetime(value, format='%d.%m.%Y %H:%M'):
        return value.strftime(format)


def register_loggers(app):
    """Initialize and configure logging."""
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
