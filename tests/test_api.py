# -*- coding: utf-8 -*-
"""API tests using WebTest.
"""
import pytest

from dribdat.user.models import Event

from .factories import EventFactory


@pytest.mark.usefixtures('db')
class TestEvents:
    """Login."""

    def test_get_event_data(self, testapp):
        """Get basic event data."""
        event = Event(name="test")
        event.save()
        res = testapp.get('/api/events.json')
        assert res.status_code == 200
        assert len(res.json['events']) == 1
        assert res.json['events'][0]['name'] == "test"
        # Test the same in CSV format
        res = testapp.get('/api/events.csv')
        assert '"test"' in res

