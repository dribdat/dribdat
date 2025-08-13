# -*- coding: utf-8 -*-
"""Helper functions for authentication steps."""
from flask_dance.contrib import (slack, azure, github, gitlab)
from dribdat.sso import (oauth2, mattermost, hitobito)


def get_auth_blueprint(app):
    """Read configuration to produce a Flask-Dance blueprint."""
    if 'OAUTH_TYPE' not in app.config or not app.config['OAUTH_TYPE']:
        return None
    blueprint = None
    oauth_type = app.config['OAUTH_TYPE']
    if oauth_type == 'slack':
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
    elif oauth_type == 'azure':
        blueprint = azure.make_azure_blueprint(
            client_id=app.config['OAUTH_ID'],
            client_secret=app.config['OAUTH_SECRET'],
            tenant=app.config['OAUTH_DOMAIN'],
            scope="profile email User.ReadBasic.All openid",
            redirect_to="auth.azure_login",
            login_url="/login",
        )
    elif oauth_type == 'github':
        blueprint = github.make_github_blueprint(
            client_id=app.config['OAUTH_ID'],
            client_secret=app.config['OAUTH_SECRET'],
            scope='user:email',
            redirect_to="auth.github_login",
            login_url="/login",
        )
    elif oauth_type == 'gitlab':
        if app.config['OAUTH_DOMAIN']:
            blueprint = gitlab.make_gitlab_blueprint(
                client_id=app.config['OAUTH_ID'],
                client_secret=app.config['OAUTH_SECRET'],
                hostname=app.config['OAUTH_DOMAIN'],
                redirect_to="auth.gitlab_login",
                login_url="/login",
                scope='read_user'
            )
        else:
            blueprint = gitlab.make_gitlab_blueprint(
                client_id=app.config['OAUTH_ID'],
                client_secret=app.config['OAUTH_SECRET'],
                redirect_to="auth.gitlab_login",
                login_url="/login",
                scope='read_user'
            )
    elif oauth_type == 'oauth2':
        if not app.config['OAUTH_DOMAIN']:
            raise Exception("Please specify an OAUTH_DOMAIN")
        blueprint = oauth2.make_oauth2_blueprint(
            client_id=app.config['OAUTH_ID'],
            secret=app.config['OAUTH_SECRET'],
            base_url=app.config['OAUTH_DOMAIN'],
            scope=app.config['OAUTH_SCOPE'] or 'openid,profile,email',
            redirect_to="auth.oauth2_login",
            login_url="/login",
        )
    elif oauth_type == 'mattermost':
        blueprint = mattermost.make_mattermost_blueprint(
            client_id=app.config['OAUTH_ID'],
            secret=app.config['OAUTH_SECRET'],
            domain=app.config['OAUTH_DOMAIN'],
            redirect_to="auth.mattermost_login",
            login_url="/login",
        )
    elif oauth_type == 'hitobito':
        blueprint = hitobito.make_hitobito_blueprint(
            client_id=app.config['OAUTH_ID'],
            secret=app.config['OAUTH_SECRET'],
            domain=app.config['OAUTH_DOMAIN'],
            scope='name',
            redirect_to="auth.hitobito_login",
            login_url="/login",
        )
    return blueprint
