# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for

from dribdat.user.models import User, Project

from dribdat.public.project import revert_project_by_activity

from .factories import UserFactory, ProjectFactory, EventFactory


class TestEditing:
    """Editing functional tests"""

    def test_log_in_and_edit(self, user, testapp):
        """Login successful."""
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()
        assert res.status_code == 200
        # Fills out the new event form 
        res1 = testapp.get('/event/new')
        form1 = res1.forms[0]
        form1['name'] = 'New Event'
        res1 = form1.submit().follow()
        assert res1.status_code == 200
        # Fills out the add project form
        res2 = testapp.get('/project/event/1/project/new')
        form2 = res2.forms[0]
        form2['name'] = 'New Project'
        res2 = form2.submit().follow()
        assert res2.status_code == 200
        # A new project was created
        assert len(Project.query.all()) == 1

    def test_sees_error_message_if_passwords_dont_match(self, user, testapp):
        """Show error if passwords don't match."""
        # Goes to registration page
        res = testapp.get(url_for('auth.register'))
        # Fills out form, but passwords don't match
        form = res.forms['registerForm']
        form['username'] = 'foobar'
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['confirm'] = 'secrets'
        # Submits
        res = form.submit()
        # sees error message
        assert 'Passwords must match' in res

    def test_sees_error_message_if_user_already_registered(self, user, testapp):  # type: ignore # noqa
        """Show error if user already registered."""
        user = UserFactory(active=True)  # A registered user
        user.save()
        # Goes to registration page
        res = testapp.get(url_for('auth.register'))
        # Fills out form, but username is already registered
        form = res.forms['registerForm']
        form['username'] = user.username
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['confirm'] = 'secret'
        # Submits
        res = form.submit()
        # sees error
        assert 'A user with this name already exists' in res

    def test_edit_and_revert(self, db, testapp):
        """Test reverting projects."""
        user = UserFactory(active=True, is_admin=True)
        user.set_password('myprecious')
        user.save()
        # Login with the user
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()
        assert res.status_code == 200
        event = EventFactory()
        event.save()
        project = ProjectFactory()
        project.event = event
        project.save()
        # A new project was created: edit it
        res1 = testapp.get('/project/%d/edit' % project.id)
        form1 = res1.forms['projectEdit']
        form1['longtext'] = "Hello"
        res1 = form1.submit().follow()
        assert res1.status_code == 200
        # Change the content now
        res2 = testapp.get('/project/%d/edit' % project.id)
        form2 = res2.forms['projectEdit']
        form2['longtext'] = "Fixme"
        res2 = form2.submit().follow()
        assert res2.status_code == 200
        # Get previous activity and revert to it
        activity = project.activities[-2]
        assert activity.project_version is not None
        result, status = revert_project_by_activity(project, activity)
        assert result is not None
        # Check that we have indeed reverted to original text
        project = Project.query.first()
        assert 'Hello' == project.longtext
