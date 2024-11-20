# -*- coding: utf-8 -*-
"""Helper functions for user lists."""

from dribdat.user.models import User, Activity
from urllib.parse import quote, quote_plus
from flask import flash

from sqlalchemy import or_

import re


# Removes markdown and HTML tags
RE_NO_TAGS = re.compile(r'\!\[[^\]]*\]\([^\)]+\)|\[|\]|<[^>]+>')


def get_users_by_search(search_by, MAX_COUNT=200):
    """Collects all users."""
    users = User.query.filter_by(active=True)
    if search_by and len(search_by) > 2:
        q = search_by.replace('@', '').lower()
        q = "%%%s%%" % q
        if '@' in search_by:
            users = users.filter(or_(
                User.email.ilike(q),
                User.username.ilike(q)
            ))
        else:
            users = users.filter(or_(
                User.my_story.ilike(q),
                User.my_goals.ilike(q),
            ))
    # TODO: pagination!
    if users.count() > MAX_COUNT:
        # Only the first 200 participants are shown
        users = users.limit(MAX_COUNT)
    # Provide certificate if available
    if users:
        return sorted(users.all(), key=lambda x: x.username)
    return []


def filter_users_by_search(users, search_by=None, role_call=None):
    """Collects the participating users."""
    if not users: return [], ''
    # Quick (actually, rather slow..) search filter:
    if role_call and len(role_call) > 2:
        usearch = []
        for u in users:
            for r in u.roles:
                if role_call in str(r):
                    usearch.append(u)
                    search_by = role_call
                    break
    elif search_by and len(search_by) > 2:
        usearch = []
        qq = search_by.replace('@', '').lower()
        for u in users:
            if qq in u.username.lower() or qq in u.email.lower():
                usearch.append(u)
            elif (u.my_story and qq in u.my_story.lower()) or \
                 (u.my_goals and qq in u.my_goals.lower()):
                usearch.append(u)
    else:
        usearch = users
        search_by = ''
    return usearch, search_by


def get_dribs_paginated(page=1, per_page=10, host_url=''):
    """Collects the latest activities ("dribs")."""
    latest_dribs = Activity.query.filter(or_(
        Activity.action == "post",
        Activity.name == "boost")).order_by(Activity.id.desc())
    dribs = latest_dribs.paginate(page=page, per_page=per_page)
    dribs.items = [
        d for d in dribs.items
        if not d.project.is_hidden and d.content]
    # Generate social links
    for d in dribs.items:
        d.share = {
            'text': quote(" ".join([
                RE_NO_TAGS.sub('', d.content or d.project.name),
                d.project.event.hashtags or '#dribdat']).strip()),
            'url': quote_plus(host_url + d.project.url)
        }
    return dribs


def get_user_by_name(username):
    """ Retrieves a user by name """
    if not username:
        return None
    username = username.strip()
    if not username:
        return None
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Username %s not found!' % username, 'warning')
        return None
    return user
