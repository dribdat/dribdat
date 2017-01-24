# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash
from datetime import datetime

def random_password():
    import string, random
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))

def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)

def timesince(dt, default="just now", until=False):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    - from http://flask.pocoo.org/snippets/33/
    """
    now = datetime.utcnow()
    if dt is None: return ""
    if until and dt > now:
        diff = dt - now
        suffix = "to go"
    else:
        diff = now - dt
        suffix = "ago"
    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )
    for period, singular, plural in periods:
        if round(period) > 0:
            return "%d %s %s" % (period, singular if period == 1 else plural, suffix)
    return default
