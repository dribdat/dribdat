# -*- coding: utf-8 -*-
"""Dribdat feature tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for

from dribdat.user.models import Project

from .factories import ProjectFactory

from dribdat.onebox import make_onebox

class TestProjects:
    """Project features."""

    def test_onebox(self, project, testapp):
        """Generate one box."""

        test_markdown = """Some project content
<p><a href="http://127.0.0.1:5000/project/%d">http://127.0.0.1:5000/project/%d</a></p>
EOF""" % (project.id, project.id)

        result = make_onebox(test_markdown)
        assert 'onebox' in result
