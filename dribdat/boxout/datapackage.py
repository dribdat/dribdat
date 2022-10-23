"""Boxout module for Data Packages."""

import re
import logging
import pystache
from frictionless import Package

TEMPLATE_PACKAGE = r"""
<div class="boxout datapackage card mb-4" style="max-width:23em">
  <div class="card-body">
    <a href="{{homepage}}">
        <h5 class="card-title font-weight-bold">{{title}}</h5>
    </a>
    <a href="{{url}}" download>
        <h6 class="card-subtitle mb-2 text-muted">Data Package</h6>
    </a>
    <div class="card-text description">{{description}}</div>
    <ul class="resources list-unstyled">
    {{#resources}}
        <li><a href="{{path}}" download class="card-link">{{name}}</a>
        <span class="schema-fields">{{#schema.fields}}
            <b title="{{type}}">&#9632;</b>
        {{/schema.fields}}</span></li>
    {{/resources}}
    </ul>
    <div class="details font-size-small">
        <div class="sources float-left">&#128230;
        {{#sources}}
            <a href="{{path}}">{{name}}</a>
        {{/sources}}
        </div>
        {{#licenses}}
        <i class="created">{{created}}</i>
            &nbsp;
        <i class="version">{{version}}</i>
            &nbsp;
        <a class="license" target="_top"
           href="{{path}}" title="{{title}}">License</a>
        {{/licenses}}
    </div>
  </div>
</div>
"""

dpkg_url_re = re.compile(r'.*(http?s:\/\/.+datapackage\.json)\)*')


def box_datapackage(line):
    """Create a OneBox for local projects."""
    m = dpkg_url_re.match(line)
    if not m:
        return None
    url = m.group(1)
    try:
        package = Package(url)
    except Exception:  # noqa: B902
        logging.info("Data Package not parsed: <%s>" % url)
        return None
    return pystache.render(TEMPLATE_PACKAGE, package)
