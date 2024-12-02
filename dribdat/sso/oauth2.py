from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Oleg Lavrovsky <oleg@datalets.ch>"


def make_oauth2_blueprint(
    client_id: str,
    secret: str,
    base_url: str,
    *,
    scope: str="",
    redirect_url: str="",
    redirect_to: str="",
    login_url: str="",
    authorized_url: str="",
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with any OAuth 2 provder. This requires
    an OAuth consumer. Pass the client ID and secret and URL to this constructor,
    or make sure that the Flask application config defines them, using the variables:
    :envvar:`OAUTH2_CLIENT_DOMAIN`,
    :envvar:`OAUTH2_CLIENT_ID` and
    :envvar:`OAUTH2_CLIENT_SECRET`.
    Args:
        client_id (str): The OAuth2 Client ID for your application
        secret (str): The OAuth2 Client Secret for your application
        base_url (str): URL with base path to the authentication endpoint
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
    oauth2_bp = OAuth2ConsumerBlueprint(
        "oauth2",
        __name__,
        client_id=client_id,
        client_secret=secret,
        scope=scope.split(','),
        base_url=baseurl,
        authorization_url=baseurl + "/authorize",
        token_url=baseurl + "/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    oauth2_bp.from_config["base_url"] = "OAUTH2_CLIENT_DOMAIN"
    oauth2_bp.from_config["client_id"] = "OAUTH2_CLIENT_ID"
    oauth2_bp.from_config["client_secret"] = "OAUTH2_CLIENT_SECRET"

    @oauth2_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_oauth2 = oauth2_bp.session

    return oauth2_bp


oauth2 = LocalProxy(lambda: g.flask_dance_oauth2)
