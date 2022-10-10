from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Oleg Lavrovsky <oleg@datalets.ch>"


def make_auth0_blueprint(
    client_id=None,
    secret=None,
    domain=None,
    *,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Auth0 using OAuth 2. This requires
    an OAuth consumer from Auth0. Either pass the domain, client ID and secret
    to this constructor, or make sure that the Flask application config defines
    them, using the variables :envvar:`AUTH0_CLIENT_DOMAIN`,
    :envvar:`AUTH0_CLIENT_ID` and
    :envvar:`AUTH0_CLIENT_SECRET`.
    Args:
        client_id (str): The Auth0 Client ID for your application
        secret (str): The Auth0 Client Secret for your application
        domain (str): The Auth0 Domain for your application
        scope (str, optional): comma-separated list of scopes for OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/login``
        authorized_url (str, optional): URL path for the ``authorized`` view.
            Defaults to ``/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be
            passed when adding the login and authorized routes. Defaults to
            ``None``.
    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to Flask app.
    """
    scope = scope or ["email", "profile", "openid"]
    auth0_bp = OAuth2ConsumerBlueprint(
        "auth0",
        __name__,
        client_id=client_id,
        client_secret=secret,
        scope=scope,
        base_url="https://" + domain,
        authorization_url="https://" + domain + "/authorize",
        token_url="https://" + domain + "/oauth/token",
        # token_url_params={"include_client_id": True},
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    auth0_bp.from_config["base_url"] = "AUTH0_CLIENT_DOMAIN"
    auth0_bp.from_config["client_id"] = "AUTH0_CLIENT_ID"
    auth0_bp.from_config["client_secret"] = "AUTH0_CLIENT_SECRET"

    @auth0_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_auth0 = auth0_bp.session

    return auth0_bp


auth0 = LocalProxy(lambda: g.flask_dance_auth0)
