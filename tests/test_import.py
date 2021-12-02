# -*- coding: utf-8 -*-
"""Dribdat data import export tests.
"""
from flask import url_for
import pytest

from dribdat.user.models import Event, Project, Activity, User, Role

from dribdat.apipackage import ImportEventPackage, PackageEvent

from .factories import *


class TestImport:
    """Sample import export."""

    def test_datapackage(self, project, testapp):
        """Create a data package."""

        event = Event(name="Test Event", summary="Just testin")
        event.save()

        role = Role(name="Test Role")
        role.save()

        user = UserFactory(username="Test Author")
        user.roles.append(role)
        user.save()

        proj1 = Project(name="Test Project")
        proj1.event = event
        proj1.user = user
        proj1.save()

        acty1 = Activity("review", proj1.id)
        acty1.content = "Hello World!"
        acty1.save()

        dp_json = PackageEvent(event, user)
        assert dp_json.title == "Test Event"

        acty1.delete()
        proj1.delete()
        event.delete()

        assert Event.query.filter_by(name="Test Event").count() is 0

        event_import = ImportEventPackage(dp_json)
        assert Event.query.filter_by(name="Test Event").count() is 1
