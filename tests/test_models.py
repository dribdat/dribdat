# -*- coding: utf-8 -*-
"""Model unit tests."""

from datetime import datetime

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
class TestUser:
    """User tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User('foo', 'foo@bar.com')
        user.save()

        retrieved = User.get_by_id(user.id)
        assert retrieved == user

        newdata = { 'username': 'bar', 'webpage_url': '#' }
        user.set_from_data(newdata)
        assert user.username == 'bar'
        assert user.webpage_url == newdata['webpage_url']
        assert 'localdomain' not in user.email

        user = User()
        user.set_from_data(newdata)
        assert 'localdomain' in user.email

    def test_created_at_defaults_to_datetime(self):
        """Test creation date."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert bool(user.created_at)
        assert isinstance(user.created_at, datetime)

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

    def test_social(self):
        """Check social network profile."""
        user = UserFactory()
        user.socialize()
        assert user.cardtype == ''
        assert 'gravatar' in user.carddata
        user.webpage_url = 'https://github.com/dribdat'
        user.socialize()
        assert user.cardtype == 'github'
        assert 'dribdat' in user.carddata
        user.webpage_url = 'https://gitlab.com/dribdat'
        user.email = b64decode(b'b2xAdXRvdS5jaA==').decode("utf-8")
        user.socialize()
        assert user.cardtype == 'gitlab'
        assert 'identicon' in user.carddata
        user.webpage_url = 'https://linkedin.com/in/loleg'
        user.socialize()
        assert user.cardtype == 'linkedin-square'
        assert 'avatar' in user.carddata

    def test_user_score(self, db):
        """Profile completeness scores."""
        project = ProjectFactory()
        project.progress = 30
        project.save()
        user1 = UserFactory()
        user1.save()
        assert user1.get_score() == 0
        user1.webpage_url = 'https://blah.com'
        user1.save()
        assert user1.get_score() == 2
        ProjectActivity(project, 'star', user1)
        project.update_now()
        assert user1.get_score() == 9
        project.longtext = 'lorem'.join('ipsum' for i in range(999))
        project.update_now()
        assert len(project.longtext) > 500
        assert user1.get_score() == 10
        project.progress = 80
        project.update_now()
        assert user1.get_score() == 20
