# -*- coding: utf-8 -*-
"""API tests using WebTest.
"""
import pytest
import json

from dribdat.aggregation import ProjectActivity
from dribdat.apigenerate import gen_project_pitch
from dribdat.user.models import Event
from dribdat.public.api import *

from .factories import EventFactory, ProjectFactory, UserFactory


@pytest.mark.usefixtures('db')
class TestApi:
    """API and data import/export tests."""

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

        # Test iCalendar compliance
        icaldata = info_event_ical(event.id)
        assert 'VEVENT' in icaldata
        assert event.name in icaldata


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

        # Test participants
        user1 = UserFactory()
        user2 = UserFactory()
        project = ProjectFactory()
        project.user = user1
        project.event = event
        project.save()
        ProjectActivity(project, 'star', user1)
        ProjectActivity(project, 'star', user2)
        assert project in user1.joined_projects()
        assert project not in user1.joined_projects(False) # no challenges

        # Test event API
        userlist = get_users_for_event(event, True)
        assert user1.username in [ u['username'] for u in userlist ]
        assert user2.username in [ u['username'] for u in userlist ]
        assert project.name in [ u['teams'] for u in userlist ]
        assert 'score' in userlist[0]


    def test_get_platform_data(self):
        """More global data types."""
        event = EventFactory(name="hello")
        user = UserFactory()
        project = ProjectFactory()
        project.user = user
        project.event = event
        project.longtext = "Smee"
        project.progress = 0
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
