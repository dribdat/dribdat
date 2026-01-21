# -*- coding: utf-8 -*-
"""Helper functions for user lists."""

from dribdat.user.models import User, Activity, Role
from urllib.parse import quote, quote_plus
from flask import flash
from dribdat.database import db
from sqlalchemy import func, case

from sqlalchemy import or_, and_

import re


# Removes markdown and HTML tags
RE_NO_TAGS = re.compile(r'\!\[[^\]]*\]\([^\)]+\)|\[|\]|<[^>]+>')


def get_users_by_search(search_by, MAX_COUNT=200):
    """Collects all users."""
    if not search_by or len(search_by) < 3:
        return []
    users = User.query.filter_by(active=True)
    q = search_by.replace('@', '').replace('*', '').replace('~', '')
    q = "%%%s%%" % q.lower()
    if search_by.startswith('*'):
        # We are looking for a skill
        users = users.filter(or_(
            User._my_skills.ilike(q),
            User._my_wishes.ilike(q)
        ))
    elif search_by.startswith('~'):
        # We are looking for a role
        a_role = Role.query.filter(Role.name.ilike(q)).first()
        if not a_role:
            return []
        users = users.filter(User.roles.contains(a_role))
    elif '@' in search_by:
        # Looking for a username or email
        users = users.filter(or_(
            User.email.ilike(q),
            User.username.ilike(q),
            User.fullname.ilike(q),
        ))
    else:
        # General search
        users = users.filter(or_(
            User.my_story.ilike(q),
            User.my_goals.ilike(q),
            User.username.ilike(q),
            User.fullname.ilike(q),
        ))
    if not users:
        return []
    # Filter to active, limit, sort
    users = users.limit(MAX_COUNT).all()
    return sorted(users, key=lambda x: x.username)


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

def get_contributor_stats():
    """Gathers statistics about contributors."""
    stmt = db.session.query(
        User.id,
        User.username,
        func.count(Activity.id).label('total_activities'),
        func.sum(case((Activity.action == 'commit', 1), else_=0)).label('commits'),
        func.sum(case((Activity.action == 'post', 1), else_=0)).label('comments')
    ).join(Activity, User.id == Activity.user_id).group_by(User.id).subquery()

    results = db.session.query(
        stmt.c.username,
        stmt.c.total_activities,
        stmt.c.commits,
        stmt.c.comments
    ).order_by(stmt.c.total_activities.desc()).all()

    return results
