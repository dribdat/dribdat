# -*- coding: utf-8 -*-
"""Jinja formatters for Oneboxes and Embeds."""

import re
import pystache
import logging

from flask import url_for

from micawber import parse_text
from micawber.parsers import standalone_url_re, full_handler


def format_webembed(url):
    if url.lower().startswith('<iframe '):
        return url
    if url.startswith('https://query.wikidata.org/'):
        url = url.replace('https://query.wikidata.org/', 'https://query.wikidata.org/embed.html')
    # TODO: add more embeddables
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
    if mat == None:
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
            if not project: return mat.group()
            pd = project.data
            pd['link'] = project_link
            return pystache.render(TEMPLATE_PROJECT, pd)
    return mat.group()

def make_onebox(raw_html):
    url = re.escape(url_for('.home', _external=True))
    regexp = re.compile('<a href="(%s.+?)">(%s.+?)</a>' % (url, url))
    return re.sub(regexp, repl_onebox, raw_html)

def make_oembedplus(text, oembed_providers, **params):
    lines = text.splitlines()
    parsed = []
    home_url = re.escape(url_for('.home', _external=True))
    home_url_re = re.compile('(%s.+)' % home_url)
    for line in lines:
        if home_url_re.match(line):
            line = re.sub(home_url_re, repl_onebox, line)
        elif standalone_url_re.match(line):
            url = line.strip()
            try:
                response = oembed_providers.request(url, **params)
            except Exception as e:
                logging.warning("OEmbed provider could not be parsed <%s>" % url)
            else:
                line = full_handler(url, response, **params)
        parsed.append(line)
    return '\n'.join(parsed)
