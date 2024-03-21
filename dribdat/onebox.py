# -*- coding: utf-8 -*-
"""Jinja formatters for Oneboxes and Embeds."""

import re
import logging
from flask import url_for
from micawber.parsers import standalone_url_re, full_handler
from .boxout.ckan import box_dataset, chk_dataset, ini_dataset
from .boxout.dribdat import box_project
from .boxout.datapackage import box_datapackage, chk_datapackage
from .boxout.github import box_repo
from dribdat.extensions import cache


def format_webembed(url, project_id):
    """Create a well-formatted frame for project embeds."""
    if not url:
        return ''
    urltest = url.lower().strip()
    if urltest.startswith('<iframe '):
        # Allow IFRAMEs
        # TODO: add a setting
        return url
    elif urltest.endswith('.pdf'):
        # Redirect to embed visualizer of this document
        url = url_for('project.render', project_id=project_id)
    elif urltest.startswith('https://query.wikidata.org/'):
        # Fix WikiData queries
        url = url.replace('https://query.wikidata.org/',
                          'https://query.wikidata.org/embed.html')
    elif urltest.startswith('https://youtu.be/'):
        # Fix YouTube mobile link
        url = url.replace('https://youtu.be/',
                          'https://www.youtube.com/embed/')
        url = url.replace('?t=', '?start=')
    elif urltest.startswith('https://www.youtube.com/watch?'):
        # Fix YouTube web link
        url = url.replace('https://www.youtube.com/watch?v=',
                          'https://www.youtube.com/embed/')
        url = url.replace('?t=', '?start=')
    # TODO: add more embeddables here
    # TODO: whitelist
    return '<iframe src="%s"></iframe>' % url


def repl_onebox(mat=None, li=[]):
    """Check for onebox application links."""
    if mat is None:
        li[:] = []
        return
    if mat.group(1):
        url = mat.group(1).strip()
        if '/project/' in url:
            # Try to parse a project link
            return box_project(url) or mat.group()
    return mat.group()


def make_onebox(raw_html):
    """Create a onebox container."""
    url = re.escape(url_for('public.home', _external=True))
    regexp = re.compile('<a href="(%s.+?)">(%s.+?)</a>' % (url, url))
    return re.sub(regexp, repl_onebox, raw_html)


def make_oembedplus(text, oembed_providers, **params):
    """Check for additional onebox lines."""
    lines = text.splitlines()
    parsed = []
    has_dataset = False
    # Url to projects
    home_url = re.escape(url_for('public.home', _external=True) + 'project/')
    home_url_re = re.compile('(%s.+)' % home_url)
    # Iterate each line (inefficient!)
    for line in lines:
        newline = None
        if home_url_re.match(line):
            # Parse an internal project
            newline = re.sub(home_url_re, repl_onebox, line)
        elif chk_datapackage(line):
            # Try to parse a Data Package link
            newline = box_datapackage(line, cache)
        elif chk_dataset(line):
            # Try to render a CKAN dataset link
            newline = box_dataset(line)
            has_dataset = has_dataset or newline is not None
        #elif line.startswith('https://github.com/'):
            # Try to parse a GitHub link
        #    newline = box_repo(line)
        elif standalone_url_re.match(line):
            # Check for out of box providers
            newline = box_default(line, oembed_providers, **params)
        # Do we have parse?
        if newline is not None:
            line = newline
        parsed.append(line)
    # Add init code
    if has_dataset:
        parsed = [ini_dataset()] + parsed
    return '\n'.join(parsed)


def box_default(line, oembed_providers, **params):
    """Fetch a built-in provider box."""
    url = line.strip()
    try:
        response = oembed_providers.request(url, **params)
    except Exception:  # noqa: B902
        logging.info("OEmbed could not parse: <%s>" % url)
    else:
        return full_handler(url, response, **params)
    return None
