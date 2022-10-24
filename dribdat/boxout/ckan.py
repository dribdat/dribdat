"""Boxout module for CKAN datasets."""

import pystache
import logging

TEMPLATE_PACKAGE = r"""
<div class="boxout ckan card mb-4">
  <div class="card-body" id="ckan-embed-1">
    <a href="{{url}}" target="_blank" rel="noopener noreferrer">{{url}}</a>
  </div>
  <script src="https://cdn.jsdelivr.net/gh/opendata-swiss/ckan-embed/dist/ckan-embed.bundle.js"></script>
  <script>
    CKANembed.dataset('#ckan-embed-1', '{{url}}');
  </script>
</div>
"""


def box_dataset(url):
    """Create a OneBox for local projects."""
    box = pystache.render(TEMPLATE_PACKAGE, { 'url': url })
    return box
