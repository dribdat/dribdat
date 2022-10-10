# -*- coding: utf-8 -*-
"""Helper functions for authentication steps."""
from flask_dance.contrib import (slack, azure, github)
from dribdat.sso import (auth0, mattermost)


def get_auth_blueprint(app):
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
    elif app.config['OAUTH_TYPE'] == 'auth0':
        blueprint = auth0.make_auth0_blueprint(
            client_id=app.config['OAUTH_ID'],
            secret=app.config['OAUTH_SECRET'],
            domain=app.config['OAUTH_DOMAIN'],
            redirect_to="auth.auth0_login",
            login_url="/login",
        )
    elif app.config['OAUTH_TYPE'] == 'mattermost':
        blueprint = mattermost.make_mattermost_blueprint(
            client_id=app.config['OAUTH_ID'],
            secret=app.config['OAUTH_SECRET'],
            domain=app.config['OAUTH_DOMAIN'],
            redirect_to="auth.mattermost_login",
            login_url="/login",
        )
    return blueprint
