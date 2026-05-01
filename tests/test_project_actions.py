# -*- coding: utf-8 -*-
import pytest
from flask import url_for
from dribdat.user.models import Project, Activity
from .factories import UserFactory, ProjectFactory, EventFactory
from dribdat.aggregation import ProjectActivity

@pytest.mark.usefixtures('db')
class TestProjectActions:

    def test_project_star_me(self, testapp, user):
        """Test starring a project."""
        event = EventFactory()
        project = ProjectFactory(event=event)
        project.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        # Star project
        res = testapp.get(f'/project/{project.id}/star/me').follow()
        assert res.status_code == 200
        assert project.name in res.text
        # Verify activity
        assert Activity.query.filter_by(name='star', project_id=project.id, user_id=user.id).count() == 1

    def test_project_unstar_me(self, testapp, user):
        """Test unstarring a project."""
        event = EventFactory()
        project = ProjectFactory(event=event)
        project.save()
        ProjectActivity(project, 'star', user)

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        # Unstar project
        res = testapp.get(f'/project/{project.id}/unstar/me').follow()
        assert res.status_code == 200
        # Verify activity is gone
        assert Activity.query.filter_by(name='star', project_id=project.id, user_id=user.id).count() == 0

    def test_project_autoupdate(self, testapp, user):
        """Test autoupdating a project."""
        event = EventFactory()
        project = ProjectFactory(autotext_url='https://github.com/user/repo', event=event)
        project.user = user
        project.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        from unittest.mock import patch
        with patch('dribdat.public.project.GetProjectData') as mock_data, \
             patch('dribdat.public.project.SyncProjectData') as mock_sync:
            mock_data.return_value = {'name': 'Updated Name', 'type': 'github', 'autotext': 'Content'}
            res = testapp.get(f'/project/{project.id}/autoupdate').follow()
            assert res.status_code == 200
            mock_sync.assert_called_once()

    def test_project_log(self, testapp):
        """Test project log view."""
        event = EventFactory()
        project = ProjectFactory(event=event)
        project.save()
        res = testapp.get(f'/project/{project.id}/log')
        assert res.status_code == 200

    def test_project_toggle(self, testapp, user):
        """Test toggling project status (hidden/visible)."""
        # Set user as admin to bypass AllowProjectEdit restrictions on hidden projects
        user.is_admin = True
        user.save()

        event = EventFactory()
        project = ProjectFactory(is_hidden=False, event=event)
        project.user = user
        project.save()
        pid = project.id

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        # Toggle (becomes hidden)
        res = testapp.get(f'/project/{pid}/toggle')
        assert res.status_code == 302
        assert Project.query.get(pid).is_hidden == True

    def test_project_post(self, testapp, user):
        """Test posting to a project."""
        event = EventFactory()
        project = ProjectFactory(event=event)
        project.user = user
        project.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        res = testapp.get(f'/project/{project.id}/post')
        form = res.forms[0]
        form['note'] = 'Test post content'
        res = form.submit().follow()
        assert 'Test post content' in res.text

    def test_project_comment(self, testapp, user):
        """Test commenting on a project."""
        event = EventFactory()
        project = ProjectFactory(event=event)
        project.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        res = testapp.get(f'/project/{project.id}/comment')
        form = res.forms[0]
        form['note'] = 'Test comment content'
        res = form.submit().follow()
        assert 'feedback' in res.text
