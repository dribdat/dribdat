# -*- coding: utf-8 -*-
"""Feeds for dribdat."""
import boto3
import datetime as dt

from flask import (
    Blueprint, current_app, render_template,
    Response, request, redirect, url_for
)
from flask_login import current_user
from sqlalchemy import or_
from datetime import datetime
from ..user.models import Event, Project, Activity, User
from ..apiutils import (
    get_event_activities,
)

blueprint = Blueprint('feeds', __name__, url_prefix='/feeds')

MAX_ITEMS = 20
RSS_DATE_FORMAT = '%a %d %b %Y %H:%M %Z'

# ------ FEEDS ---------

def rssheader(resp):    
    resp.headers['Content-Type'] = 'application/rss+xml'
    return resp


@blueprint.route("/dribs")
def get_dribs():
    """Show the latest logged posts."""
    dribs = Activity \
            .query \
            .filter(or_(
                Activity.action == "post",
                Activity.name == "boost")) \
            .order_by(Activity.id.desc()) \
            .limit(MAX_ITEMS)
    activities = [
        d for d in dribs
        if not d.project.is_hidden and d.content]
    if len(activities) > 0:
        event = activities[0].project.event
    else:
        event = current_event()
    now = datetime.utcnow().strftime(RSS_DATE_FORMAT)
    fqdn = url_for("public.event", event_id=event.id, _external=True)
    atomlink = url_for("feeds.get_dribs", _external=True)
    return render_template("public/rss.xml",
                           now=now,
                           title=event.name,
                           fqdn=fqdn,
                           description=event.summary,
                           atomlink=atomlink,
                           activities=activities)


@blueprint.route('/user/<username>', methods=['GET'])
def get_user(username):
    """Output feed by username."""
    a_user = User.query.filter_by(username=username).first_or_404()
    url_profile = url_for("public.user", username=un, _external=True)
    activities = a_user.latest_posts(MAX_ITEMS)
    return 'Not implemented'
