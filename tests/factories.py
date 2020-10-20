# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from factory import PostGenerationMethodCall, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from dribdat.database import db
from dribdat.user.models import User, Project


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

    class Meta:
        """Factory configuration."""

        model = User

class ProjectFactory(BaseFactory):
    """Project factory."""

    name = Sequence(lambda n: 'Project {0}'.format(n))
    summary = "Just a test project"
    image_url = "http://image.local/something.png"
    webpage_url = "http://webpage.localhost"
    logo_color = "red"

    class Meta:
        """Factory configuration."""

        model = Project
