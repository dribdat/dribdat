# -*- coding: utf-8 -*-
"""Jinja formatters for Oneboxes and Embeds."""

import re
import pystache
import logging

from flask import url_for

from micawber.parsers import standalone_url_re, full_handler


def format_webembed(url):
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


TEMPLATE_PROJECT = r"""
<div class="onebox">
<a href="{{link}}">
<img src="{{image_url}}" />
<h5 class="name">{{name}}</h5>
<div class="phase">{{phase}}</div>
<p>{{summary}}</p>
</a>
</div>
"""


def repl_onebox(mat=None, li=[]):
    if mat is None:
        li[:] = []
        return
    if mat.group(1):
        url = mat.group(1).strip()
        # Try to parse a project link
        if '/project/' in url:
            project_link = mat.group(1)
            project_id = int(url.split('/')[-1])
            from .user.models import Project
            project = Project.query.filter_by(id=project_id).first()
            if not project:
                return mat.group()
            pd = project.data
            # project.url returns a relative path?
            pd['link'] = project_link
            return pystache.render(TEMPLATE_PROJECT, pd)
    return mat.group()


def make_onebox(raw_html):
    url = re.escape(url_for('public.home', _external=True))
    regexp = re.compile('<a href="(%s.+?)">(%s.+?)</a>' % (url, url))
    return re.sub(regexp, repl_onebox, raw_html)


def make_oembedplus(text, oembed_providers, **params):
    lines = text.splitlines()
    parsed = []
    home_url = re.escape(url_for('public.home', _external=True))
    home_url_re = re.compile('(%s.+)' % home_url)
    for line in lines:
        if home_url_re.match(line):
            line = re.sub(home_url_re, repl_onebox, line)
        elif standalone_url_re.match(line):
            url = line.strip()
            try:
                response = oembed_providers.request(url, **params)
            except Exception:
                logging.info("OEmbed could not parse: <%s>" % url)
            else:
                line = full_handler(url, response, **params)
        parsed.append(line)
    return '\n'.join(parsed)


def github_onebox(project_repo='dribdat/dribdat'):
    """Create a OneBox for GitHub repositories with issue list."""
    project_repo = project_repo.replace('https://github.com/', '')
    return '<div class="widget widget-github">' + \
        '<div data-theme="default" data-width="400" data-height="160" ' + \
        'data-github="' + project_repo + \
        '" class="github-card"></div><script src="//' + \
        'cdn.jsdelivr.net/github-cards/latest/widget.js"></script>' + \
        '<div id="issues-list" data-github="' + project_repo + \
        '" class="list-group list-data"><i>Loading ...</i></div></div>'
