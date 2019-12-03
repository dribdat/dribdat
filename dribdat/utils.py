# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, current_app
from datetime import datetime
from math import floor
import pytz
import logging
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
    timezone = pytz.timezone(current_app.config["TIME_ZONE"])
    now = timezone.localize(datetime.now())
    dt = dt.astimezone(timezone)
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
        if floor(period) > 0:
            return "%d %s %s" % (period, singular if period == 1 else plural, suffix)
    return default

def format_date(value, format='%Y-%m-%d'):
    return value.strftime(format)

def format_date_range(starts_at, ends_at):
    if starts_at.month == ends_at.month:
        if starts_at.day == ends_at.day:
            dayrange = starts_at.day
        else:
            dayrange = "{0} - {1}".format(
                starts_at.day,
                ends_at.day
            )
        return "{0} {1}, {2}".format(
            starts_at.strftime("%B"),
            dayrange,
            ends_at.year,
        )
    else:
        return "{0} {1}, {2} - {3} {4}, {5}".format(
            starts_at.strftime("%B"),
            starts_at.day,
            starts_at.year,
            ends_at.strftime("%B"),
            ends_at.day,
            ends_at.year,
        )

def format_webembed(url):
    if url.lower().startswith('<iframe '):
        return url
    if url.startswith('https://query.wikidata.org/'):
        url = url.replace('https://query.wikidata.org/', 'https://query.wikidata.org/embed.html')
    # TODO: add more embeddables
    return '<iframe src="%s"></iframe>' % url
