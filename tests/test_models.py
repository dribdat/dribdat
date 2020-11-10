# -*- coding: utf-8 -*-
"""Model unit tests."""
import datetime as dt

import pytest
import pytz

from dribdat.user.models import Role, User, Event
from dribdat.utils import timesince
from dribdat.settings import Config

from .factories import UserFactory


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
        assert timesince(event.countdown, until=True) == "%d hours to go" % timediff_hours
