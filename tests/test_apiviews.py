# -*- coding: utf-8 -*-
"""API tests using WebTest.
"""
import pytest
import json

from dribdat.apigenerate import gen_project_pitch
from dribdat.public.api import *

from .factories import (
    EventFactory, ProjectFactory, UserFactory, 
    CategoryFactory, ActivityFactory,
)


@pytest.mark.usefixtures('project')
class TestApiViews:
    """API view tests."""
    
    def test_hackathon_json(self):
        res = info_event_current_hackathon_json().json
        assert "@type" in res
        assert res['@type'] == "Hackathon" 
    
    def test_project_list(self): 
        event = Event.query.first()
        event.projects[0].progress = 0
        res = project_list_current_json().json
        assert "event" in res
        assert len(res["projects"]) == 1
        assert 'Project' in res["projects"][0]["name"]
        res = project_list_json(event.id).json
        assert 'Project' in res["projects"][0]["name"]
        res = project_list_event_csv(event.id)
        assert res.status_code == 200
        assert b"Project" in res.data
        res = project_list_current_csv()
        assert b"Project" in res.data

    def test_category_list(self):
        category1 = CategoryFactory()
        category2 = CategoryFactory(name="Another category")
        event1 = EventFactory(name="Another event")
        event2 = EventFactory()
        category2.event = event1
        category2.save()
        res = categories_list_current_json().json
        assert 'categories' in res
        assert len(res['categories']) == 1
        res = categories_list_json(event1.id).json
        assert len(res['categories']) == 2 

    def test_activity_list(self):
        event = Event.query.first()
        project = event.projects[0]
        activity1 = ActivityFactory(project_id=project.id)
        activity2 = ActivityFactory(project_id=project.id)
        res = event_activity_json(event.id).json
        assert len(res['activities']) == 2 
        res = event_activity_current_json().json
        assert len(res['activities']) == 2 
        res = event_posts_json(event.id).json
        assert len(res['activities']) == 0 
        activity3 = ActivityFactory(project_id=project.id, action="post")
        res = event_posts_current_json().json
        assert len(res['activities']) == 1
        res = projects_posts_json().json
        assert len(res['activities']) == 1
        res = project_activity_json(project.id).json
        assert len(res['activities']) == 3
    
    def test_project_info(self):
        event = Event.query.first()
        project = event.projects[0]
        activity1 = ActivityFactory(project_id=project.id)
        res = project_info_json(project.id).json
        assert 'project' in res
        assert 'stats' in res
        assert 'team' in res
        assert res['stats']['total'] == 1
        user1 = UserFactory()
        activity2 = ActivityFactory(
            project_id=project.id, user_id=user1.id, name="star"
        )
        res = project_search_json().json
        assert 'projects' in res
        assert res['projects'] == []
        data = {
            'hashtag': '#test'
        }
        project = set_project_values(project, data)
        assert project.hashtag == '#test'

    def test_event_status(self):
        event = Event.query.first()
        res = event_get_status().json
        assert 'status' in res
        assert res['status'] == ''
        event.is_current = True
        event.set_status('hello')
        event.save()
        res = event_get_status().json
        assert res['status'] == 'hello'
    

    """
    def test_get_autochallenge(self):
        # Check the new AI project form.
        project = ProjectFactory()
        project.longtext = "Smeeagain"
        project.save()
        return
        autogen = gen_project_pitch(project)
        # TODO: minimal inline model?
        assert autogen is None
        #print(autogen)
        #assert "Smee" in autogen
    """
