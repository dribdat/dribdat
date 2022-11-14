"""Boxout module for Data Packages."""

import re
import logging
import pystache
from datetime import datetime
from frictionless import Package

TEMPLATE_PACKAGE = r"""
<div class="boxout datapackage card mb-4" style="max-width:23em">
  <div class="card-body">
    <h5 class="card-title font-weight-bold">
        {{dp.title}}
    </h5>
    <h6 class="card-subtitle mb-2 text-muted">
        Data Package
        <a href="{{dp.homepage}}" title="Home page">
            &#127760;&nbsp;www
        </a>
        <a href="{{url}}" download title="Get Data Package">
            &#127760;&nbsp;json
        </a>
    </h6>
    <div class="card-text description">{{dp.description}}</div>
    <ul class="resources list-unstyled">
    {{#dp.resources}}
        <li><a href="{{path}}" download class="card-link">{{name}}</a>
        <span class="schema-fields">{{#schema.fields}}
            <b title="{{type}}">&#9632;</b>
        {{/schema.fields}}</span></li>
    {{/dp.resources}}
    </ul>
    <div class="details font-size-small">
        <div class="sources float-left">
        {{#dp.sources}}
            <a href="{{path}}">&#128230; {{title}}</a>
        {{/dp.sources}}
        </div>
        <small title="Date" class="created">{{date}}</small>
            &nbsp;
        <i title="Version" class="version">{{dp.version}}</i>
            &nbsp;
        {{#dp.licenses}}
            <a class="license" target="_top"
               href="{{path}}" title="{{title}}">License</a>
        {{/dp.licenses}}
    </div>
  </div>
</div>
"""

dpkg_url_re = re.compile(r'.*(http?s:\/\/.+datapackage\.json)\)*')


def chk_datapackage(line):
    """Check the url matching dataset pattern."""
    return (
        (line.startswith('http') and line.endswith('datapackage.json'))
        or line.endswith('datapackage.json)'))


def box_datapackage(line, cache=None):
    """Create a OneBox for local projects."""
    m = dpkg_url_re.match(line)
    if not m:
        return None
    url = m.group(1)
    if cache and cache.has(url):
        return cache.get(url)
    try:
        logging.info("Fetching Data Package: <%s>" % url)
        package = Package(url)
    except Exception:  # noqa: B902
        logging.warn("Data Package not parsed: <%s>" % url)
        return None
    if package.created:
        dt = datetime.fromisoformat(package.created).strftime("%d.%m.%Y")
    else:
        dt = ''
    box = pystache.render(
        TEMPLATE_PACKAGE, {'url': url, 'dp': package, 'date': dt})
    if cache:
        cache.set(url, box)
    if cache and cache.has(url):
        logging.debug("Cached Data Package: <%s>" % url)
    return box
