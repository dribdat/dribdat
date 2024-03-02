# -*- coding: utf-8 -*-
"""Model unit tests."""

import datetime as dt

import pytest
import pytz

from dribdat.user.models import Role, User, Event
from dribdat.user.constants import stageProjectToNext
from dribdat.utils import timesince
from dribdat.settings import Config
from dribdat.aggregation import ProjectActivity
from dribdat.boxout.dribdat import box_project

from .factories import UserFactory, ProjectFactory, EventFactory


@pytest.mark.usefixtures('db')
class TestUser:
    """User tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User('foo', 'foo@bar.com')
        user.save()

        retrieved = User.get_by_id(user.id)
        assert retrieved == user

    def test_created_at_defaults_to_datetime(self):
        """Test creation date."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert bool(user.created_at)
        assert isinstance(user.created_at, dt.datetime)

    def test_password_is_nullable(self):
        """Test null password."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert user.password is None

    def test_factory(self, db):
        """Test user factory."""
        user = UserFactory(password='myprecious')
        db.session.commit()
        assert bool(user.username)
        assert bool(user.email)
        assert bool(user.created_at)
        assert user.is_admin is False
        assert user.active is True
        assert user.check_password('myprecious')

    def test_check_password(self):
        """Check password."""
        user = User.create(username='foo', email='foo@bar.com',
                           password='foobarbaz123')
        assert user.check_password('foobarbaz123') is True
        assert user.check_password('barfoobaz') is False

    def test_roles(self):
        """Add a role to a user."""
        role = Role(name='admin')
        role.save()
        user = UserFactory()
        user.roles.append(role)
        user.save()
        assert role in user.roles


@pytest.mark.usefixtures('db')
class TestEvent:
    """Event tests."""

    def test_countdown_10_days(self, db):
        timezone = pytz.timezone(Config.TIME_ZONE)
        now = dt.datetime.now()
        event_dt = now + dt.timedelta(days=10)
        event = Event(name="test", starts_at=event_dt)
        event.save()

        assert event.starts_at == event_dt  # store as naive
        assert event.name == "test"
        assert event.countdown is not None
        assert event.countdown == timezone.localize(event_dt)
        assert timesince(event.countdown, until=True) == "1 week to go"

    def test_countdown_24_days(self, db):
        now = dt.datetime.now()
        timezone = pytz.timezone(Config.TIME_ZONE)
        event_dt = now + dt.timedelta(days=24)
        event = Event(name="test", starts_at=event_dt)
        event.save()

        assert event.starts_at == event_dt  # store as naive
        assert event.name == "test"
        assert event.countdown is not None
        assert event.countdown == timezone.localize(event_dt)
        assert timesince(event.countdown, until=True) == "3 weeks to go"

    def test_countdown_4_hours(self, db):
        timezone = pytz.timezone(Config.TIME_ZONE)
        now = dt.datetime.now()
        tz_now = timezone.localize(dt.datetime.utcnow())
        # need to add 10 seconds to avoid timesince to compute 3.9999h
        # formated to 3 by timesince
        event_dt = now + dt.timedelta(hours=4, seconds=10)
        event = Event(name="test", starts_at=event_dt)
        event.save()

        tz_event = timezone.localize(event_dt)
        timediff = tz_event - tz_now
        timediff_hours = timediff.total_seconds()//3600

        assert event.starts_at == event_dt  # store as naive
        assert event.name == "test"
        assert event.countdown is not None
        assert event.countdown == tz_event
        assert timesince(
            event.countdown, until=True) == "%d hours to go" % timediff_hours

    def test_event_projects(self, db):
        event = EventFactory()
        event.save()
        p1 = ProjectFactory()
        p1.event = event
        p1.save()
        p2 = ProjectFactory()
        p2.event = event
        p2.save()
        p3 = ProjectFactory()
        p3.event = event
        p3.is_hidden = True
        p3.save()
        assert event.project_count == 2
        assert p1 in event.current_projects()
        assert p3 not in event.current_projects()


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
        stageProjectToNext(project)
        project.update_now()
        assert project.versions.count() == 2
        challenge = project.as_challenge().revert()
        assert challenge.name != TEST_NAME
        challenge.update_now()
        challenge.save()
        assert challenge.versions.count() == 2

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
