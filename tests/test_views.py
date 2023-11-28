# -*- coding: utf-8 -*-
"""Dribdat view tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from .factories import ProjectFactory, EventFactory, UserFactory
from dribdat.public import views
from dribdat.aggregation import ProjectActivity
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

        # Test the print view
        view_html = testapp.get('/event/%d/print' % event.id)
        assert 'All projects' in view_html

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

        # Test personal view
        user_rss = testapp.get('/feeds/user/' + user.username)
        assert 'Hello, world' in user_rss
