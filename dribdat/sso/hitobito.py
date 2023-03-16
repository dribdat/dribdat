from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Oleg Lavrovsky <oleg@datalets.ch>"


def make_hitobito_blueprint(
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
    Make a blueprint for authenticating with hitobito using OAuth 2. Requires
    an OAuth consumer from hitobito. Either pass the domain, ID, secret
    to this constructor, or make sure that the Flask application config defines
    them, using the variables :envvar:`hitobito_CLIENT_DOMAIN`,
    :envvar:`hitobito_CLIENT_ID` and
    :envvar:`hitobito_CLIENT_SECRET`.
    Args:
        client_id (str): The hitobito Client ID for your application
        secret (str): The hitobito Client Secret for your application
        domain (str): The hitobito Domain for your application
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
    scope = scope or ['']
    hitobito_bp = OAuth2ConsumerBlueprint(
        "hitobito",
        __name__,
        client_id=client_id,
        client_secret=secret,
        scope=scope,
        base_url="https://" + domain,
        authorization_url="https://" + domain + "/oauth/authorize",
        token_url="https://" + domain + "/oauth/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    hitobito_bp.from_config["base_url"] = "HITOBITO_CLIENT_DOMAIN"
    hitobito_bp.from_config["client_id"] = "HITOBITO_CLIENT_ID"
    hitobito_bp.from_config["client_secret"] = "HITOBITO_CLIENT_SECRET"

    @hitobito_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_hitobito = hitobito_bp.session

    return hitobito_bp


hitobito = LocalProxy(lambda: g.flask_dance_hitobito)
