# -*- coding: utf-8 -*-
"""Feeds for dribdat."""
import boto3

from flask import (
    Blueprint, current_app, render_template,
    Response, request, redirect, url_for
)
from flask_login import current_user
from sqlalchemy import or_

from dateutil import parser
from datetime import datetime, UTC

from ..user.models import Event, Project, Activity, User
from ..apiutils import (
    get_event_activities,
)

blueprint = Blueprint('feeds', __name__, url_prefix='/feeds')

MAX_ITEMS = 20
RSS_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

# ------ FEEDS ---------


@blueprint.route("/dribs.xml")
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
        d.data for d in dribs
        if not d.project.is_hidden and d.content]
    atomlink = url_for("feeds.get_dribs", _external=True)
    fqdn = url_for("public.dribs", _external=True)
    return format_rss_feed("Latest dribs", fqdn, atomlink, activities)


@blueprint.route('/user/<username>', methods=['GET'])
def get_user(username):
    """Output feed by username."""
    a_user = User.query.filter_by(username=username).first_or_404()
    atomlink = url_for("feeds.get_user", username=username, _external=True)
    fqdn = url_for("public.user_profile", username=username, _external=True)
    activities = a_user.latest_posts(MAX_ITEMS)
    return format_rss_feed("Dribs by " + a_user.name, fqdn, atomlink, activities)


def format_rss_feed(title, fqdn, atomlink, activities):
    """Return an RSS formatted feed."""
    now = datetime.now(UTC).strftime(RSS_DATE_FORMAT)
    for a in activities:
        a['rssdate'] = parser.parse(a['date']).strftime(RSS_DATE_FORMAT)
    html = render_template("public/rss.xml",
                           now=now,
                           fqdn=fqdn,
                           atomlink=atomlink,
                           title=title,
                           description='Latest updates from Dribdat',
                           activities=activities)
    resp = Response(html)
    resp.headers['Content-Type'] = 'application/rss+xml'
    return resp
