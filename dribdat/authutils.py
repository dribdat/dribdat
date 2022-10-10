# -*- coding: utf-8 -*-
"""Helper functions for authentication steps."""
from flask_dance.contrib import (slack, azure, github)


def get_blueprint(app):
    """Read configuration to produce a Flask-Dance blueprint."""
    if 'OAUTH_TYPE' not in app.config or not app.config['OAUTH_TYPE']:
        return None
    blueprint = None
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
    return blueprint
