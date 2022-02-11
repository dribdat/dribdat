# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, current_app
from datetime import datetime
from math import floor
from os import path

import pytz, re, csv, yaml

def strtobool(text):
    """ Truthy conversion as per PEP 632 """
    tls = str(text).lower().strip()
    if tls in ['y', 'yes', 't', 'true', 'on', '1']:
        return True
    if tls in ['n', 'no', 'f', 'false', 'off', '0']:
        return False
    raise ValueError("{} is not convertable to boolean".format(tls))

def sanitize_input(text):
    """ Removes unsavoury characters """
    return re.sub(r"[^a-zA-Z0-9_]+", '', text)

def random_password(pwdlen=20):
    """ A strongly secure random string """
    import string, random
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(pwdlen))

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
    if dt is None: return ""
    tz = pytz.timezone(current_app.config["TIME_ZONE"])
    tz_now = tz.localize(dt.utcnow())
    dt = dt.astimezone(tz)
    if dt is None: return ""
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
            return "%d %s %s" % (period, singular if int(period)==1 else plural, suffix)
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

""" Load event preset content """
def load_event_presets():
    EVENT_PRESET = {
        'eventstart': '',
        'quickstart': '',
        'codeofconduct': '',
    }
    for pr in EVENT_PRESET.keys():
        fn = path.join(path.join(path.join(
            path.dirname(__file__),
                'templates'), 'includes'), pr + '.md')
        with open(fn, mode='r') as file:
            EVENT_PRESET[pr] = file.read()
    return EVENT_PRESET

""" Load structured settings from a CSV file """
def load_csv_presets(filename, by_col='name'):
    fn = path.join(path.join(path.join(
        path.dirname(__file__), 'templates'), 'includes'), filename + '.csv')
    settings_dict = {}
    with open(fn, mode='r') as file:
        csvreader = csv.DictReader(file, delimiter=';')
        for row in csvreader:
            settings_dict[row[by_col]] = row
    return settings_dict

""" Load structured settings from a YAML file """
def load_yaml_presets(filename, by_col='name'):
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
