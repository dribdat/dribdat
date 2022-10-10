# -*- coding: utf-8 -*-
"""Jinja formatters for Oneboxes and Embeds."""

import re
import pystache
import logging

from flask import url_for

from .user.models import Project

from micawber.parsers import standalone_url_re, full_handler


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


def project_onebox(url):
    """Create a OneBox for local projects."""
    project_id = url.split('/')[-1]
    if not project_id:
        return None
    project = Project.query.filter_by(id=int(project_id)).first()
    if not project:
        return None
    pd = project.data
    # project.url returns a relative path
    pd['link'] = url
    return pystache.render(TEMPLATE_PROJECT, pd)


TEMPLATE_GITHUB = r"""
<div class="widget widget-github">
<div data-theme="default" data-width="400" data-height="160"
     data-github="{{repo}}" class="github-card"></div>
<script src="//cdn.jsdelivr.net/github-cards/latest/widget.js"></script>
<div id="issues-list" data-github="{{repo}}"
     class="list-group list-data"><i>Loading ...</i></div>
</div>
"""


def github_onebox(url='dribdat/dribdat'):
    """Create a OneBox for GitHub repositories with issue list."""
    project_repo = url.replace('https://github.com/', '').strip()
    if not project_repo:
        return None
    return pystache.render(TEMPLATE_GITHUB, {'repo': project_repo})


def repl_onebox(mat=None, li=[]):
    """Check and onebox application links."""
    if mat is None:
        li[:] = []
        return
    if mat.group(1):
        url = mat.group(1).strip()
        if url.startswith('https://github.com/'):
            # Try to parse a GitHub link
            return github_onebox(url) or mat.group()
        elif '/project/' in url:
            # Try to parse a project link
            return project_onebox(url) or mat.group()
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
