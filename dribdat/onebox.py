# -*- coding: utf-8 -*-
"""Jinja formatters for Oneboxes and Embeds."""

import re
import logging
from flask import url_for
from micawber.parsers import standalone_url_re, full_handler
from .boxout.dribdat import box_project
from .boxout.datapackage import box_datapackage
from .boxout.github import box_repo


def format_webembed(url):
    """Create a well-formatted frame for project embeds."""
    if url.lower().startswith('<iframe '):
        # Allow IFRAMEs
        # TODO: add a setting
        return url
    if url.startswith('https://query.wikidata.org/'):
        # Fix WikiData queries
        url = url.replace('https://query.wikidata.org/',
                          'https://query.wikidata.org/embed.html')
    elif url.startswith('https://youtu.be/'):
        # Fix YouTube mobile link
        url = url.replace('https://youtu.be/',
                          'https://www.youtube.com/embed/')
    elif url.startswith('https://www.youtube.com/watch?'):
        # Fix YouTube web link
        url = url.replace('https://www.youtube.com/watch?v=',
                          'https://www.youtube.com/embed/')
    # TODO: add more embeddables here
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
    # Url to projects
    home_url = re.escape(url_for('public.home', _external=True) + 'project/')
    home_url_re = re.compile('(%s.+)' % home_url)
    # Iterate each line (inefficient!)
    for line in lines:
        newline = None
        if home_url_re.match(line):
            # Parse an internal project
            newline = re.sub(home_url_re, repl_onebox, line)
        elif (line.endswith('datapackage.json') or
              line.endswith('datapackage.json)')):
            # Try to parse a Data Package link
            newline = box_datapackage(line)
        elif line.startswith('https://github.com/'):
            # Try to parse a GitHub link
            newline = box_repo(line)
        elif standalone_url_re.match(line):
            # Check for out of box providers
            url = line.strip()
            try:
                response = oembed_providers.request(url, **params)
            except Exception:  # noqa: B902
                logging.info("OEmbed could not parse: <%s>" % url)
            else:
                newline = full_handler(url, response, **params)
        if newline is not None:
            line = newline
        parsed.append(line)
    return '\n'.join(parsed)
