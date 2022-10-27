# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, current_app
from math import floor
from os import path

import pytz
import re
import csv
import yaml


def strtobool(text):
    """Truthy conversion as per PEP 632."""
    tls = str(text).lower().strip()
    if tls in ['y', 'yes', 't', 'true', 'on', '1']:
        return True
    if tls in ['n', 'no', 'f', 'false', 'off', '0']:
        return False
    raise ValueError("{} is not convertable to boolean".format(tls))


def sanitize_input(text):
    """Remove unsavoury characters."""
    return re.sub(r"[^a-zA-Z0-9_]+", '', text)


def random_password(pwdlen=20):
    """Provide a strongly secure random string."""
    import string
    import random
    return ''.join(random.SystemRandom()
                   .choice(string.ascii_uppercase + string.digits)
                   for _ in range(pwdlen))


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(
                getattr(form, field).label.text, error), category)


def timesince(dt, default="just now", until=False):
    """Return a string representing 'time since'."""
    """E.g.: 3 days ago, 5 hours ago etc.
    See http://flask.pocoo.org/snippets/33/
    """
    if dt is None:
        return ""
    tz = pytz.timezone(current_app.config["TIME_ZONE"])
    tz_now = tz.localize(dt.utcnow())
    dt = dt.astimezone(tz)
    if dt is None:
        return ""
    if until and dt > tz_now:
        diff = dt - tz_now
        suffix = "to go"
    else:
        diff = tz_now - dt
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
            return "%d %s %s" % (
                period, singular if int(period) == 1
                else plural, suffix
            )
    return default


def format_date(value, format='%Y-%m-%d'):
    """Return a standard format of a date."""
    return value.strftime(format)


def format_date_range(starts_at, ends_at):
    """Return a formatted date range."""
    if starts_at.month == ends_at.month and starts_at.year == ends_at.year:
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
        starts_year = ""
        if starts_at.year != ends_at.year:
            starts_year = ", %d" % starts_at.year
        return "{0} {1}{2} - {3} {4}, {5}".format(
            starts_at.strftime("%B"),
            starts_at.day,
            starts_year,
            ends_at.strftime("%B"),
            ends_at.day,
            ends_at.year,
        )


def load_event_presets():
    """Load event preset content."""
    event_preset = {
        'eventstart': '',
        'quickstart': '',
        'codeofconduct': '',
    }
    for pr in event_preset.keys():
        fn = path.join(path.join(path.join(
            path.dirname(__file__),
            'templates'), 'includes'), pr + '.md')
        with open(fn, mode='r') as file:
            event_preset[pr] = file.read()
    return event_preset


def load_csv_presets(filename, by_col='name'):
    """Load structured settings from a CSV file."""
    fn = path.join(path.join(path.join(
        path.dirname(__file__), 'templates'), 'includes'), filename + '.csv')
    settings_dict = {}
    with open(fn, mode='r') as file:
        csvreader = csv.DictReader(file, delimiter=';')
        for row in csvreader:
            settings_dict[row[by_col]] = row
    return settings_dict


def load_yaml_presets(filename, by_col='name'):
    """Load structured settings from a YAML file."""
    # Expects filename to not have an extension
    # and be equivalent to the top level element
    fn = path.join(path.join(path.join(
        path.dirname(__file__), 'templates'), 'includes'), filename + '.yaml')
    settings_dict = {}
    with open(fn, mode='r') as file:
        stages = yaml.safe_load(file)
        for row in stages[filename]:
            settings_dict[row[by_col]] = row
    return settings_dict
