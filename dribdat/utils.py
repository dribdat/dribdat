# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, current_app
from urllib.parse import quote
from math import floor
from os import path

from datetime import datetime
from pytz import timezone
from .futures import UTC

from markupsafe import Markup
from markdown_it import MarkdownIt

from yaml import safe_load
from json import loads
from csv import DictReader
from random import SystemRandom

import re, string


# Instantiate Markdown parser
md = MarkdownIt('gfm-like').enable('table')

def markdownit(content):
    """ Converts a value to Markdown """
    return Markup(md.render(content))

def strtobool(text):
    """Truthy conversion as per PEP 632."""
    tls = str(text).lower().strip()
    if tls in ['y', 'yes', 't', 'true', 'on', '1']:
        return True
    if tls in ['n', 'no', 'f', 'false', 'off', '0']:
        return False
    raise ValueError("{} is not convertable to boolean".format(tls))

def get_any_key(obj, keys=[], default=''):
    """Returns the value of a dict of any key, else default"""
    for k in keys:
        if k in obj:
            return obj[k]
    return default

def sanitize_input(text):
    """Remove unsavoury characters."""
    return re.sub(r"[^a-zA-Z0-9_]+", '', text)


def sanitize_url(url):
    """Ensures a URL is just a URL."""
    return quote(url, safe='/:?&')

def unpack_csvlist(packed, sep=","):
    result = []
    if packed:
        for elem in packed.split(sep):
            s = elem.strip()
            if not s in result:
                result.append(s)
    return result

def pack_csvlist(ls, sep=","):
    if ls:
        return sep.join(ls)
    else:
        return None


def random_password(pwdlen=20):
    """Provide a strongly secure random string."""
    return ''.join(SystemRandom()
                   .choice(string.ascii_uppercase + string.digits)
                   for _ in range(pwdlen))


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(
                getattr(form, field).label.text, error), category)


def get_time_note():
    """Construct a time zone message."""
    tz = timezone(current_app.config["TIME_ZONE"])
    aware_time = datetime.now().astimezone(tz)
    tzinfo = "Server time: %s" % aware_time.strftime('%H:%M%z')
    if tz is not None:
        return "%s (%s)" % (tzinfo, tz)
    return tzinfo


def timesince(dtsince, default="just now", until=False):
    """Return a string representing 'time since'."""
    """E.g.: 3 days ago, 5 hours ago etc.
    See http://flask.pocoo.org/snippets/33/
    """
    if dtsince is None:
        return ""
    dt_now = datetime.now(UTC)
    dt = dtsince.astimezone(UTC)
    if dt is None:
        return ""
    if until and dt > dt_now:
        diff = dt - dt_now
        suffix = "" # "to go"
    else:
        diff = dt_now - dt
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


def format_date(value, format='%Y-%m-%dT%H:%M'):
    """Return a standard format of a date."""
    return value.strftime(format)


def parse_date(value, format='%Y-%m-%dT%H:%M'):
    """Parse a standard format of a date from a string."""
    if not isinstance(value, str): return value
    return datetime.strptime(value, format)


def format_date_range(starts_at, ends_at):
    """Return a formatted date range."""
    if starts_at.month == ends_at.month and starts_at.year == ends_at.year:
        if starts_at.day == ends_at.day:
            dayrange = starts_at.day
        else:
            dayrange = "{0} – {1}".format(
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
        return "{0} {1}{2} – {3} {4}, {5}".format(
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
        'terms': '',
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
    # Expects filename to *not* have a .csv extension
    fn = path.join(path.join(path.join(
        path.dirname(__file__), 'templates'), 'includes'), filename + '.csv')
    settings_dict = {}
    with open(fn, mode='r') as file:
        csvreader = DictReader(file, delimiter=';')
        for row in csvreader:
            settings_dict[row[by_col]] = row
    return settings_dict


def load_presets(stagedata, top_element='stages', by_col='name'):
    """Load presets as a dictionary."""
    settings_dict = {}
    stages = safe_load(stagedata)
    for row in stages[top_element]:
        settings_dict[row[by_col]] = row
    return settings_dict


def load_yaml_presets(filename, by_col='name', filepath=None):
    """Load structured settings from a YAML file."""
    original_filename = filename
    if not (filename.endswith('.yaml') or filename.endswith('.yml')):
        filename = filename + '.yaml'
    fn = path.join(filepath or path.join(path.join(
        path.dirname(__file__), 'templates'), 'includes'), filename)
    with open(fn, mode='r') as file:
        config = load_presets(file, original_filename, by_col)
    return config


def load_json_presets(filename, filepath=None):
    """Load structured settings from a JSON file."""
    if not (filename.endswith('.json')):
        filename = filename + '.json'
    fn = path.join(filepath or path.join(path.join(
        path.dirname(__file__), 'templates'), 'includes'), filename)
    with open(fn, mode='r') as file:
        config = loads(file.read())
    return config


def fix_relative_links(readme, imgroot, repo_full_name, default_branch):
    """Ensures that images in Markdown are absolute."""
    readme = re.sub(
        r" src=\"(?!http)",
        " src=\"%s/%s/%s/" % (imgroot, repo_full_name, default_branch),
        readme
    )
    readme = re.sub(
        r"\!\[(.*)\]\((?!http)",
        # Pass named group to include full path in the image URL
        r"![\g<1>](%s/%s/%s/" % (imgroot, repo_full_name, default_branch),
        readme
    )
    return readme


def get_random_alphanumeric_string(length=24):
    """ Get a reasonably secure password """
    return ''.join(
        (SystemRandom().choice(string.ascii_letters + string.digits)
         for i in range(length)))
