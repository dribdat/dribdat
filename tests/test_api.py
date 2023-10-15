# -*- coding: utf-8 -*-
"""API tests using WebTest.
"""
import pytest
import json

from dribdat.aggregation import ProjectActivity
from dribdat.user.models import Event
from dribdat.public.api import *

from .factories import (
    EventFactory, ProjectFactory, 
    UserFactory, ActivityFactory
)


@pytest.mark.usefixtures('db')
class TestApi:
    """API and data import/export tests."""


    def test_feed_activitypub(self, testapp):
        """ActivityPub support."""
        event = EventFactory(name="hello")
        user = UserFactory()
        project = ProjectFactory()
        ProjectActivity(project, 'star', user)
        ProjectActivity(project, 'update', user, 'post', "Test note")
        assert len(user.latest_posts(10)) == 1

        res1 = testapp.get('/feed/u/%s' % user.username)
        assert res1.status_code == 200
        assert 'activity+json' in res1.headers['Content-Type']
        assert res1.json['name'] == user.username
        assert 'publicKeyPem' in res1.json['publicKey']

        res2 = testapp.get(res1.json['outbox'])
        assert res2.status_code == 200
        assert res2.json['totalItems'] == 1
        assert res2.json['orderedItems'][0]['object']['content'] == "Test note"

        res3 = testapp.post(res1.json['inbox'])
        assert res3.status_code == 202


    def test_api_events(self):
        """Test event API functions."""
        event = EventFactory(name="hello")
        event.save()

        # Test basic event metadata
        jsondata = json.loads(info_current_event_json().data)
        assert "hello" == jsondata["event"]["name"]
        jsondata = json.loads(info_event_json(event.id).data)
        assert "hello" == jsondata["event"]["name"]

        # Test Schema.org compliance
        jsondata = json.loads(info_event_hackathon_json(event.id).data)
        # TODO: use https://github.com/schemaorg/schemarama for full validation
        assert "hello" == jsondata["name"]
        assert "Hackathon" == jsondata["@type"]
        assert "http://schema.org" == jsondata["@context"]


    def test_get_event_data(self, testapp):
        """Get basic event data."""
        event = Event(name="test")
        event.save()

        # Check event in JSON format
        res = testapp.get('/api/events.json')
        assert res.status_code == 200
        assert len(res.json['events']) == 1
        assert res.json['events'][0]['name'] == "test"

        # Test the same in CSV format
        res = testapp.get('/api/events.csv')
        assert '"test"' in res


    def test_get_platform_data(self):
        """More global data types."""
        event = EventFactory(name="hello")
        user = UserFactory()
        project = ProjectFactory()
        project.user = user
        project.event = event
        project.longtext = "Smee"
        project.save()
        ProjectActivity(project, 'update', user)

        # Test all Event data
        csvdata = project_list_all_events_csv()
        csvdata = str(csvdata.get_data())
        assert "hello" in csvdata

        # Test Activities data
        csvdata = event_activity_csv(event.id)
        csvdata = str(csvdata.get_data())
        assert "update" in csvdata

        # Test project Activities
        jsondata = json.loads(projects_activity_json().get_data())
        assert len(jsondata['activities']) == 1

        # Test Project search
        ppj = json.loads(projects_top_json().get_data())
        assert len(ppj['projects']) == 1
