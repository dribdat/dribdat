# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import pytest
from webtest import TestApp

from dribdat.app import init_app
from dribdat.database import db as _db
from dribdat.settings import TestConfig

from .factories import UserFactory, ProjectFactory


@pytest.fixture(scope='function')
def app():
    """An application for the tests."""
    _app = init_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='function')
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture(scope='function')
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def user(db):
    """A user for the tests."""
    user = UserFactory(password='myprecious')
    db.session.commit()
    return user

@pytest.fixture
def project(db):
    """A project for the tests."""
    project = ProjectFactory()
    db.session.commit()
    return project
