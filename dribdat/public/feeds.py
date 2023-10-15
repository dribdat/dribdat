# -*- coding: utf-8 -*-
"""Feed subscriptions for dribdat."""
import boto3
import tempfile
import datetime as dt

from flask import (
    Blueprint, current_app,
    Response, request, redirect,
    jsonify, url_for
)
from flask_login import current_user

from ..user.models import Event, Project, Activity, User
from ..apiutils import (
    get_event_activities,
)

blueprint = Blueprint('feed', __name__, url_prefix='/feed')


# ------ FEEDS ---------

def pubonify(apub):    
    resp = jsonify(apub)
    resp.headers['Content-Type'] = 'application/activity+json'
    return resp


@blueprint.route('/u/<username>', methods=['GET'])
def get_user(username):
    """Output ActivityPub with public data by username."""
    a_user = User.query.filter_by(username=username).first_or_404()
    private_key, public_key = a_user.get_keys()
    un = a_user.username
    url_user = url_for("public.user", username=un, _external=True)
    url_inbox = url_for("feed.post_user_inbox", username=un, _external=True)
    url_outbox = url_for("feed.get_user_activities", username=un, _external=True)
    apub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": url_user,
        "inbox": url_inbox,
        "outbox": url_outbox,
        "type": "Person",
        "name": a_user.name,
        "preferredUsername": un,
        "publicKey": {
            "id": url_user + "#main-key",
            "publicKeyPem": public_key
        }
    }
    return pubonify(apub)


@blueprint.route('/u/<username>/inbox', methods=['POST'])
def post_user_inbox(username):
    current_app.logger.info(request.headers)
    current_app.logger.info(request.data)
    return Response("", status=202)


@blueprint.route('/u/<username>/activities', methods=['GET'])
def get_user_activities(username, limit=10):
    a_user = User.query.filter_by(username=username).first_or_404()
    url_user = url_for("public.user", username=a_user.username, _external=True)
    # Fetch the latest activities
    act_data = []
    for a in a_user.latest_posts(10):
        url_project = url_for("project.project_view", project_id=a['project_id'])
        url_project = url_project + '?activity=' + str(a['id'])
        act_data.append(
            {
              "@context": "https://www.w3.org/ns/activitystreams",
              "type": "Create",
              "id": url_project + '#log',
              "actor": url_user,
              "object": {
                "to": "https://www.w3.org/ns/activitystreams#Public",
                "id": url_project,
                "type": "Note",
                "published": a['date'],
                "attributedTo": url_user,
                "content": a['content'],
              },
            }
        )
    apub = {
      "@context": "https://www.w3.org/ns/activitystreams",
      "summary": username + ' - dribs',
      "type": "OrderedCollection",
      "orderedItems": act_data,
      "totalItems": len(act_data),
    }
    return pubonify(apub)
    