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


@blueprint.route('/pub/<username>', methods=['GET'])
def get_user(username):
    """Output ActivityPub with public data by username."""
    a_user = User.query.filter_by(username=username).first_or_404()
    private_key, public_key = a_user.get_keys()
    un = a_user.username
    url_user = url_for("feed.get_user", username=un, _external=True)
    url_inbox = url_for("feed.post_user_inbox", username=un, _external=True)
    url_outbox = url_for("feed.get_user_activities", username=un, _external=True)
    url_profile = url_for("public.user", username=un, _external=True)
    apub = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
        ],
        "id": url_user,
        "url": url_profile,
        "inbox": url_inbox,
        "outbox": url_outbox,
        "type": "Person",
        "name": a_user.name,
        "preferredUsername": un,
        "publicKey": {
            "id": url_user + "#main-key",
            "owner": url_user,
            "publicKeyPem": public_key
        }
    }
    if a_user.my_story or a_user.my_goals:
        apub["summary"] = a_user.my_story or a_user.my_goals
    if a_user.carddata:
        if a_user.carddata.endswith('.png'):
            apub["mediaType"] = "image/png"
        elif a_user.carddata.endswith('.jpeg') \
            or a_user.carddata.endswith('.jpg'):
            apub["mediaType"] = "image/jpeg"
        apub["icon"] = {
            "type": "Image",
            "url": a_user.carddata
        }
    return pubonify(apub)


@blueprint.route('/pub/<username>/inbox', methods=['POST'])
def post_user_inbox(username):
    return pubonify({'ok': True})


@blueprint.route('/pub/<username>/activities', methods=['GET'])
def get_user_activities(username, limit=10):
    a_user = User.query.filter_by(username=username).first_or_404()
    url_user = url_for("feed.get_user", username=username, _external=True)
    url_activity = url_for("feed.get_user_activities", username=username, _external=True)
    # Fetch the latest activities
    act_data = []
    for a in a_user.latest_posts(10):
        url_project = url_for("project.project_view", project_id=a['project_id'], _external=True)
        url_project = url_project + '?activity=' + str(a['id'])
        act_data.append(
            {
              "@context": "https://www.w3.org/ns/activitystreams",
              
              "id": url_activity + '#create-' + str(a['id']),
              "type": "Create",
              "actor": url_user,

              "object": {
                "to": "https://www.w3.org/ns/activitystreams#Public",

                "id": url_activity + '#' + str(a['id']),
                "type": "Note",
                "published": a['date'] + ':00Z',
                "attributedTo": url_user,
                "content": a['content'] + '\n' + url_project,
              }
            }
        )
    apub = {
      "@context": "https://www.w3.org/ns/activitystreams",
      "summary": username + ' - Latest Dribs',
      "type": "OrderedCollection",
      "orderedItems": act_data,
      "totalItems": len(act_data),
    }
    return pubonify(apub)
    