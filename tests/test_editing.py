# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for

from dribdat.user.models import User, Project, Event

from dribdat.aggregation import ProjectActivity, AllowProjectEdit
from dribdat.public.project import post_preview
from dribdat.public.projhelper import revert_project_by_activity, templates_from_event, project_action

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
        # Fills out the sync project form
        res2 = testapp.get('/project/new/1')
        form2 = res2.forms[0]
        form2['name'] = 'Sync Project'
        res2 = form2.submit().follow()
        assert res2.status_code == 200
        # Fills out the create project form
        res3 = testapp.get('/project/new/1?create=1')
        form3 = res3.forms[0]
        form3['name'] = 'New Project'
        res3 = form3.submit().follow()
        assert res3.status_code == 200
        # A new project was created
        assert len(Project.query.all()) == 2
        # Check that we can edit also the event
        res4 = testapp.get('/event/1/edit')
        event = Event.query.first()
        assert event.user == user
        assert res4.status_code == 200
        form4 = res4.forms['eventEdit']
        form4['name'] = 'Another Event'
        res5 = form4.submit().follow()
        assert res5.status_code == 200
        event = Event.query.first()
        assert event.name == 'Another Event'


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

        # Create an event and project
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
        assert project.versions.count() == 3

        # Change the content a third time without a request
        project.longtext = "Smee"
        project.save()
        ProjectActivity(project, 'update', user)

        # Get latest activity
        activity = project.activities[-1]
        assert activity.project_version == 3
        activity = project.activities[-2]
        assert activity.project_version == 2

        # Get first activity (created on first edit)
        activity = project.activities[0]
        assert activity.project_version == 1

        # ... and preview it
        preview = post_preview(project.id, activity.id)
        assert "archived version" in preview

        # ... and revert to it
        result, status = revert_project_by_activity(project, activity)
        assert result is not None

        # Check that we have indeed reverted to original text
        project = Project.query.first()
        assert 'Hello' == project.longtext

    def test_project_activities(self, db, testapp):
        """Test functions related to dribs."""
        project = ProjectFactory()
        event = EventFactory()
        user = UserFactory()
        project.event = event

        # Add some activities
        ProjectActivity(project, 'star', user)
        # TODO: weirdly, without this the star doesn't register
        ProjectActivity(project, 'unstar', user)
        ProjectActivity(project, 'star', user)
        ProjectActivity(project, 'update', user)
        ProjectActivity(project, 'boost', user, 'Data whiz', 'lorem ipsum')
        project_dribs = project.all_dribs()

        # event start, project joined, updated, boosted
        assert len(project_dribs) == 4
        project_badge = [s for s in project_dribs if s['name'] == 'boost']
        assert len(project_badge) == 1

    def test_create_project(self, db, testapp):
        """Test creating projects anonymously."""
        # Create an event
        event = EventFactory()
        event.save()

        # Add a new project without logging in
        res1 = testapp.get('/project/new/%d?create=1' % event.id)
        form1 = res1.forms['projectNew']
        form1['name'] = 'Hello Anon'
        res1 = form1.submit().follow()
        assert res1.status_code == 200

        # Check that we have a new project
        project = Project.query.first()
        assert 'Hello Anon' == project.name
        assert project.is_hidden


    def test_project_auth(self, db, testapp):
        """Test editing project permission."""
        event = EventFactory()
        event.save()
        project = ProjectFactory()
        project.event = event
        project.save()
        user = UserFactory(active=True)
        user.save()
        # Test the users access rights
        assert AllowProjectEdit(project, user) is False
        # Join the project
        project_action(project.id, 'star', for_user=user)
        assert AllowProjectEdit(project, user) is True
        # Leave the project
        project_action(project.id, 'unstar', for_user=user)
        assert AllowProjectEdit(project, user) is False
        # Become author of project
        project.user = user
        project.save()
        assert project.user_id == user.id
        assert AllowProjectEdit(project, user) is True
        useradmin = UserFactory(active=True, is_admin=True)
        useradmin.save()
        assert AllowProjectEdit(project, useradmin) is True


    def test_project_suggestions(self, db, testapp):
        """Test project templates."""
        event = EventFactory()
        event.lock_templates = True
        event.save()
        project1 = ProjectFactory()
        project1.event = event
        project1.save()
        project2 = ProjectFactory()
        project2.event = event
        project2.save()
        projects = templates_from_event()
        assert len(projects) == 2
