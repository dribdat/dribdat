# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for

from .factories import UserFactory, ProjectFactory, EventFactory
from dribdat.mailer import user_activation


class TestPosting:
    """Test posting activities (a.k.a. Dribs)."""

    def test_basic_posting(self, user, testapp):
        """Create a project and add some dribs."""
        
        # Make an admin user, project, and event
        admin = UserFactory(is_admin=True)
        admin.save()
        event = EventFactory()
        event.save()
        project = ProjectFactory()
        project.user = admin
        project.event = event
        project.save()

        # Login the user
        my_hash = user_activation(admin)
        res = testapp.get(url_for('auth.activate', userid=admin.id, userhash=my_hash)).follow()
        assert res.status_code == 200

        # Approve the project
        res = testapp.get(url_for('project.project_approve', project_id=project.id))
        assert res.status_code == 302
        assert project.progress == 0

        # Boost the project
        res = testapp.get(url_for('project.project_boost', project_id=project.id))
        form = res.forms['projectBoost']
        form['note'] = 'Glorious purpose'
        form['boost_type'] = 'Award'
        res = form.submit()
        assert "Award" in res.text

        # Post a drib
        res = testapp.get(url_for('project.project_post', project_id=project.id))
        form = res.forms['projectPost']
        form['note'] = 'Testing'
        res = form.submit().follow().follow()
        assert "Testing" in res.text

        # Post a comment
        res = testapp.get(url_for('project.project_comment', project_id=project.id))
        form = res.forms['projectPost']
        form['note'] = 'Commenting'
        res = form.submit().follow().follow()
        assert "Commenting" in res.text

        # Approve the project again to test reversion
        #project.longtext = "Challenge"
        #project.save()
        #res = testapp.get(url_for('project.project_approve', project_id=project.id))
        #assert res.status_code == 302
        #assert project.progress > 1
        #project.longtext = "Blahblah"
        #project.save()
        #res = testapp.get(url_for('project.get_challenge', project_id=project.id))
        #assert "Challenge" in res.text
        #res = testapp.get(url_for('project.project_view', project_id=project.id))
        #assert "Blahblah" in res.text