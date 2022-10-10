# -*- coding: utf-8 -*-
"""Jinja formatters for Oneboxes and Embeds."""

import re
import pystache
import logging

from flask import url_for

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
<div class="onebox honeycomb">
    <a class="hexagon
        {{#is_challenge}}challenge{{/is_challenge}}
        {{^is_challenge}}project{{/is_challenge}}" href="{{link}}">
<div class="hexagontent">
<span>{{name}}</span>
{{#image_url}}
<div class="hexaicon" style="background-image:url('{{image_url}}')"></div>
{{/image_url}}
</div>
    </a>
    <div class="phase">{{phase}}</div>
    <p>{{summary}}</p>
</div>
"""


def project_onebox(url):
    """Create a OneBox for local projects."""
    project_id = url.split('/')[-1]
    if not project_id:
        return None
    from .user.models import Project
    project = Project.query.filter_by(id=int(project_id)).first()
    if not project:
        return None
    pd = project.data
    # project.url returns a relative path
    pd['link'] = url
    return pystache.render(TEMPLATE_PROJECT, pd)


TEMPLATE_GITHUB = r"""
<div class="widget widget-github">
{{#issues}}
<div id="issues-list" data-github="{{repo}}" class="list-group list-data">
    <i>Loading ...</i></div>
{{/issues}}
<div data-theme="default" data-width="400" data-height="160"
     data-github="{{repo}}" class="github-card"></div>
<script src="//cdn.jsdelivr.net/github-cards/latest/widget.js"></script>
</div>
"""


def github_onebox(url='dribdat/dribdat'):
    """Create a OneBox for GitHub repositories with optional issue list."""
    project_repo = url.replace('https://github.com/', '')
    if not project_repo:
        return url
    has_issues = project_repo.endswith('/issues')
    project_repo = project_repo.replace('/issues', '')
    project_repo = project_repo.strip()
    return pystache.render(TEMPLATE_GITHUB, {
        'repo': project_repo, 'issues': has_issues})


def repl_onebox(mat=None, li=[]):
    """Check for onebox application links."""
    if mat is None:
        li[:] = []
        return
    if mat.group(1):
        url = mat.group(1).strip()
        if '/project/' in url:
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
        elif line.startswith('https://github.com/'):
            # Try to parse a GitHub link
            line = github_onebox(line)
        elif standalone_url_re.match(line):
            # Check for out of box providers
            url = line.strip()
            try:
                response = oembed_providers.request(url, **params)
            except Exception:
                logging.info("OEmbed could not parse: <%s>" % url)
            else:
                line = full_handler(url, response, **params)
        parsed.append(line)
    return '\n'.join(parsed)
