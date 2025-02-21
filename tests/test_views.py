# -*- coding: utf-8 -*-
"""Dribdat view tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from .factories import ProjectFactory, EventFactory, UserFactory, RoleFactory
from dribdat.public import views, userhelper
from dribdat.aggregation import ProjectActivity, GetEventUsers
from datetime import datetime

class TestViews:
    """Home views."""

    def test_public_views(self, event, testapp):
        """Check stage progression."""
        event = EventFactory()
        event.status = '99999999999;Hello Status'
        event.is_current = True
        event.save()
        project = ProjectFactory()
        project.event = event
        project.save()
        
        # Check the dashboard status
        view_html = testapp.get('/dashboard/')
        assert 'Hello Status' in view_html

        # Test the history view
        event2 = EventFactory()
        event2.name = 'Special Event'
        event2.ends_at = datetime(1970, 1, 1)
        event2.save()
        view_html = testapp.get('/history')
        assert 'Special Event' in view_html

        # Test the stages view
        view_html = testapp.get('/event/%d/stages' % event.id)
        assert 'Stages' in view_html

        # Test the categories view
        view_html = testapp.get('/event/%d/categories' % event.id)
        assert 'Categories' in view_html

        # Test the challenges view
        view_html = testapp.get('/event/%d/challenges' % event.id)
        assert 'Challenges' in view_html

        # Test the print view
        view_html = testapp.get('/event/%d/print' % event.id)
        assert 'Active projects' in view_html

        # Test the dribs view
        view_html = testapp.get('/dribs')
        assert 'in small amounts' in view_html
        
    def test_feeds_rss(self, event, testapp):
        """Check RSS feeds."""
        event = EventFactory()
        event.save()
        user = UserFactory()
        project = ProjectFactory()
        project.event = event
        project.user = user
        project.save()
        ProjectActivity(project, 'review', user, 'post', 'Hello, world')
        
        # Check dribs
        view_rss = testapp.get('/feeds/dribs.xml')
        assert 'content:encoded' in view_rss

        querypage = userhelper.get_dribs_paginated()
        assert len(querypage.items) == 1

        # Test personal view
        user_rss = testapp.get('/feeds/user/' + user.username)
        assert 'Hello, world' in user_rss

    def test_user_helpers(self, event, testapp):
        """Functions used in user search."""

        user = UserFactory()
        user.username = 'Bob'
        user.fullname = 'The Builder'
        user.my_story = 'Knight of Can-A-Lot'
        user._my_skills = 'hammer,time'
        user.save()
        assert user in userhelper.get_users_by_search('@bob')
        assert user in userhelper.get_users_by_search('@builder')
        assert user in userhelper.get_users_by_search('knight')
        assert user in userhelper.get_users_by_search('*hammer')

        role = RoleFactory()
        user.roles.append(role)
        user.save()
        assert user in userhelper.get_users_by_search('~' + role.name)

        user2 = UserFactory()
        user2.username = 'Bobby'
        user2.save()
        assert len(userhelper.get_users_by_search('@bob', 2)) == 2
        assert len(userhelper.get_users_by_search('@bob', 1)) == 1
        
        user_view = testapp.get('/participants?q=bob')
        assert user.username in user_view
        assert user2.username in user_view

        event = EventFactory()
        event.save()
        project = ProjectFactory()
        project.event = event
        project.save()
        ProjectActivity(project, 'star', user)
        assert project in user.joined_projects()
        users = GetEventUsers(event)
        assert user in users
