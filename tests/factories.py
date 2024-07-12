# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import PostGenerationMethodCall, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from dribdat.database import db
from dribdat.user.models import User, Project, Event, Activity
from datetime import datetime, timedelta, UTC


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""
        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    """User factory."""

    username = Sequence(lambda n: 'user{0}'.format(n))
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = PostGenerationMethodCall('set_password', 'example')
    active = True

    class Meta:  # noqa: D106
        model = User


class ProjectFactory(BaseFactory):
    """Project factory."""

    name = Sequence(lambda n: 'Project {0}'.format(n))
    summary = "Just a test project"
    image_url = "http://image.local/something.png"
    webpage_url = "http://webpage.localhost"
    logo_color = "red"

    class Meta:  # noqa: D106
        model = Project


class EventFactory(BaseFactory):
    """Event factory."""

    name = Sequence(lambda n: 'Event {0}'.format(n))
    summary = "Just a sample event"
    starts_at = datetime.now(UTC) - timedelta(hours=1)
    ends_at = datetime.now(UTC) + timedelta(days=2)

    class Meta:  # noqa: D106
        model = Event


class ActivityFactory(BaseFactory):
    """Activity factory."""

    name = "review"
    content = Sequence(lambda n: 'Activity {0}'.format(n))

    class Meta:  # noqa: D106
        model = Activity
