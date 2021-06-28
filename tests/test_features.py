# -*- coding: utf-8 -*-
"""Dribdat feature tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for
import pytest

from dribdat.user.models import Project
from dribdat.user import projectProgressList

from .factories import ProjectFactory

from dribdat.onebox import make_onebox
from dribdat.aggregation import *

class TestProjects:
    """Project features."""

    def test_onebox(self, project, testapp):
        """Generate one box."""

        srv = url_for('public.home', _external=True)
        url = "%sproject/%d" % (srv, project.id)
        test_markdown = """Some project content
<p><a href="%s">%s</a></p>
EOF""" % (url, url)

        result = make_onebox(test_markdown)
        assert 'onebox' in result
