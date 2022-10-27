"""Boxout module for CKAN datasets."""

import pystache
import random

TEMPLATE_PACKAGE = r"""
<div class="boxout ckan card mb-4">
  <div class="card-body" id="ckan-embed-{{rnd}}">
    <a href="{{url}}" target="_blank" rel="noopener noreferrer">{{url}}</a>
  </div>
  <script>
    CKANembed.dataset('#ckan-embed-{{rnd}}', '{{url}}');
  </script>
</div>
"""


def ini_dataset():
    """Initialisation script."""
    return (
        '<script src="https://cdn.jsdelivr.net/gh/'
        + 'opendata-swiss/ckan-embed/dist/ckan-embed.bundle.js"></script>'
    )


def chk_dataset(line):
    """Check the url matching dataset pattern."""
    return line.startswith('http') and '/dataset/' in line


def box_dataset(url):
    """Create a OneBox for local projects."""
    rnd = random.Random().randrange(0, 9999)
    box = pystache.render(TEMPLATE_PACKAGE, {'url': url, 'rnd': rnd})
    return box
