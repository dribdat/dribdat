# -*- coding: utf-8 -*-
"""Model unit tests."""

import pytest
import pytz
from base64 import b64decode

from dribdat.user.models import Role, User, Event
from dribdat.user.constants import stageProjectToNext
from dribdat.utils import timesince
from dribdat.settings import Config
from dribdat.aggregation import ProjectActivity
from dribdat.boxout.dribdat import box_project

from .factories import UserFactory, ProjectFactory, EventFactory

@pytest.mark.usefixtures('db')
class TestProject:
    """Project tests."""

    def test_project_factory(self, db):
        """Test factory."""
        project = ProjectFactory()
        db.session.add(project)
        db.session.commit()
        assert bool(project.name)
        assert bool(project.summary)
        assert bool(project.created_at)
        assert project.is_hidden is False
        TEST_NAME = u'Updated name'
        assert project.versions.count() == 1
        project.name = TEST_NAME
        db.session.commit()
        assert project.name == TEST_NAME
        assert project.versions.count() == 2
        project.versions[0].revert()
        assert project.name != TEST_NAME
        assert project.versions.count() == 3

    def test_project_roles(self, db):
        """Test role factory."""
        project = ProjectFactory()
        project.save()
        role1 = Role(name='a role')
        role1.save()
        role2 = Role(name='another role')
        role2.save()
        user = UserFactory()
        user.roles.append(role1)
        user.save()
        ProjectActivity(project, 'star', user)
        assert role2 in project.get_missing_roles()

    def tests_project_box(self, db):
        """Test boxed (embedded) projects."""
        project = ProjectFactory()
        project.save()
        dpkg_html = box_project(project.url)
        assert "onebox" in dpkg_html

    def test_project_score(self, db):
        """Test role factory."""
        project = ProjectFactory()
        project.save()
        assert project.is_challenge
        project.update_now()
        assert project.score == 0
        user1 = UserFactory()
        user1.save()
        ProjectActivity(project, 'star', user1)
        project.update_now()
        assert project.score == 1
        user2 = UserFactory()
        user2.save()
        ProjectActivity(project, 'star', user1)
        project.update_now()
        assert project.score == 1
        ProjectActivity(project, 'star', user2)
        project.update_now()
        assert project.score == 2
        ProjectActivity(project, 'unstar', user2)
        project.update_now()
        assert project.score == 1

    def test_project_promote(self, db):
        project = ProjectFactory()
        db.session.add(project)
        db.session.commit()
        assert project.is_challenge
        TEST_NAME = u'Updated name'
        project.name = TEST_NAME
        project.progress = 0
        stageProjectToNext(project)
        project.update_now()
        project.save()
        assert project.versions.count() == 2
        assert not project.is_challenge
        challenge = project.as_challenge()
        assert challenge.name != TEST_NAME
        challenge.update_now()
        challenge.save()
        assert challenge.versions.count() == 3

    def test_project_from_data(self):
        project = ProjectFactory()
        event = EventFactory()
        project.event = event
        project.save()
        testdata = project.data
        testdata['name'] = 'Testme'
        project2 = ProjectFactory()
        project2.set_from_data(testdata)
        project2.save()
        assert project2.name == 'Testme'
        assert project2.event == project.event

    def test_project_formatting(self):
        project = ProjectFactory()
        project.webpage_url = '<iframe src="https://12345"></iframe>'
        project.update_now()
        assert project.webpage_url == "https://12345"
        
# @pytest.mark.usefixtures('db')
# class TestResource:
#     """Resource (Component) tests."""
#
#     def test_resource_collection(self, db):
#         resourceA = Resource(name="Test A")
#         resourceA.save()
#
#         assert resourceA.name == "Test A"
#         assert getResourceType(resourceB) == 'Code'
#         assert getResourceType(resourceC) == 'Other'
#         assert getResourceType(resourceN) == 'Other'
