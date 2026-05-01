# -*- coding: utf-8 -*-
import pytest
from flask import url_for, current_app
from dribdat.user.models import User, Event
from .factories import UserFactory, ProjectFactory, EventFactory
from unittest.mock import patch

@pytest.mark.usefixtures('db')
class TestAuthEdgeCases:

    def test_enter_forgot(self, testapp):
        """Test the enter route redirection."""
        testapp.app.config['MAIL_SERVER'] = 'localhost'
        testapp.app.config['OAUTH_TYPE'] = None
        res = testapp.get('/enter/')
        assert res.status_code == 302
        assert res.location.endswith('/forgot/')

    def test_enter_login(self, testapp):
        """Test the enter route redirection when no mail server."""
        testapp.app.config['MAIL_SERVER'] = None
        res = testapp.get('/enter/')
        assert res.status_code == 302
        assert res.location.endswith('/login/')

    def test_login_skip_oauth(self, testapp):
        """Test skipping login when OAUTH_SKIP_LOGIN is set."""
        testapp.app.config['OAUTH_SKIP_LOGIN'] = True
        testapp.app.config['OAUTH_TYPE'] = 'github'
        # Mock url_for to avoid build error during test
        with patch('dribdat.public.auth.url_for') as mock_url_for:
            mock_url_for.return_value = '/github_login'
            res = testapp.get('/login/')
            assert res.status_code == 302
            assert '/github_login' in res.location

    def test_register_disabled(self, testapp):
        """Test registration when disabled."""
        testapp.app.config['DRIBDAT_NOT_REGISTER'] = True
        res = testapp.get('/register/')
        assert res.status_code == 302
        assert 'Registration currently not possible' in res.follow().text

    def test_delete_account(self, testapp, user):
        """Test deleting a user account."""
        # Create a project owned by user
        project = ProjectFactory(user=user)
        project.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        # Delete account
        res = testapp.post('/user/profile/delete')
        assert res.status_code == 302
        assert User.query.filter_by(id=user.id).first() is None
        assert project.user_id is None

    def test_user_profile_edit_sso(self, testapp, user):
        """Test editing profile for SSO user."""
        user.sso_id = 'sso123'
        user.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        res = testapp.get('/user/profile')
        # The form on this page doesn't have an id, find it by index
        form = res.forms[0]
        assert 'password' not in form.fields

    def test_user_profile_email_conflict(self, testapp, user):
        """Test editing profile with conflicting email."""
        other_user = UserFactory(email='other@example.com')
        other_user.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        res = testapp.get('/user/profile')
        form = res.forms[0]
        form['email'] = 'other@example.com'
        res = form.submit()
        assert 'This e-mail address is already registered.' in res.text

    def test_passwordless_no_mail(self, testapp):
        """Test passwordless login when mail server is not configured."""
        testapp.app.config['MAIL_SERVER'] = None
        res = testapp.post('/passwordless/')
        assert res.status_code == 302
        assert 'login' in res.location

    def test_passwordless_success(self, testapp, user):
        """Test passwordless login request."""
        testapp.app.config['MAIL_SERVER'] = 'localhost'
        res = testapp.post('/passwordless/', {'username': user.email})
        assert res.status_code == 302
        assert 'activation mail' in res.follow().text

    def test_user_ranking_no_event(self, testapp, user):
        """Test user ranking when no current event."""
        Event.query.update({Event.is_current: False})

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()

        res = testapp.get('/user/ranking')
        assert res.status_code == 302
        assert 'no current event' in res.follow().text
