# -*- coding: utf-8 -*-
"""Dribdat feature tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for
import pytest

from dribdat.user.models import Project, Resource
from dribdat.user import projectProgressList

from .factories import ProjectFactory

from dribdat.onebox import make_onebox
from dribdat.aggregation import *

class TestProjects:
    """Project features."""

    def test_onebox(self, project, testapp):
        """Generate one box."""

        srv = url_for('.home', _external=True)
        url = "%sproject/%d" % (srv, project.id)
        test_markdown = """Some project content
<p><a href="%s">%s</a></p>
EOF""" % (url, url)

        result = make_onebox(test_markdown)
        assert 'onebox' in result


@pytest.mark.usefixtures('db')
class TestProgressTree:
    """Project suggestions tests."""

    def test_resource_tree(self, db):
        rA = Resource(name="Code A", type_id=100, progress_tip=None)
        rA.save()
        rB = Resource(name="Code B", type_id=300, progress_tip=0)
        rB.save()
        rC = Resource(name="Code C", type_id=200, progress_tip=10)
        rC.save()
        rD = Resource(name="Code D", type_id=200, progress_tip=10)
        rD.save()
        rE = Resource(name="Code E", type_id=200, progress_tip=5)
        rE.save()
        rN = Resource(name="Code N", type_id=100, is_visible=False)
        rN.save()

        allres = SuggestionsByProgress()
        assert len(allres) == 5 # one is hidden
        assert allres[-1] == rB

        rTree = SuggestionsTreeForEvent()
        assert rTree[-1]['index'] == -1 # etc
        assert len(rTree) == 7 + 1 # defaults plus etc
        assert rTree[0]['resources'] == [rB] # idea or challenge
        assert rTree[1]['resources'] == [rE] # team has formed
        assert rTree[2]['resources'] == [rC, rD] # researching
        assert rTree[-1]['resources'] == [rA]
