# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for

from dribdat.user.models import User
from dribdat.mailer import (
    user_activation, 
    user_activation_message, 
    user_invitation,
    user_invitation_message,
)

from .factories import UserFactory, ProjectFactory, EventFactory


class TestLoggingIn:
    """Login."""

    def test_can_log_in_returns_200(self, user, testapp):
        """Login successful."""
        # Goes to homepage
        res = testapp.get('/login/')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200

    def test_sees_alert_on_log_out(self, user, testapp):
        """Show alert on logout."""
        res = testapp.get('/login/')
        # Fills out login form in navbar
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        res = testapp.get(url_for('auth.logout')).follow()
        # sees alert
        assert 'You are logged out.' in res

    def test_sees_error_message_if_password_is_incorrect(self, user, testapp):
        """Show error if password is incorrect."""
        # Goes to homepage
        res = testapp.get('/login/')
        # Fills out login form, password incorrect
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'wrong'
        # Submits
        res = form.submit()
        # sees error
        assert 'Invalid password' in res

    def test_sees_error_message_if_username_doesnt_exist(self, user, testapp):
        """Show error if username doesn't exist."""
        # Goes to homepage
        res = testapp.get('/login/')
        # Fills out login form, password incorrect
        form = res.forms['loginForm']
        form['username'] = 'unknown'
        form['password'] = 'myprecious'
        # Submits
        res = form.submit()
        # sees error
        assert 'Could not find your user account' in res


class TestRegistering:
    """Register a user."""

    def test_can_register(self, user, testapp):
        """Register a new user."""
        old_count = len(User.query.all())
        # Goes to homepage
        res = testapp.get('/login/')
        # Clicks Create Account button
        res = res.click('Create an account')
        # Fills out the form
        form = res.forms['registerForm']
        form['username'] = 'foobar'
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        form['confirm'] = 'secret'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200
        # A new user was created
        assert len(User.query.all()) == old_count + 1

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

    def test_admin_register(self, user, testapp):
        """Create a new user as admin."""
        user = UserFactory(active=True)  # Make an admin user
        user.set_password('myprecious')
        user.is_admin = True
        user.save()
        # Login the user
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200
        # Let's create another account
        old_count = User.query.count()
        res = testapp.get(url_for('admin.user_new'))
        # Fills out the form
        form = res.forms[0]
        form['username'] = 'foobar'
        form['email'] = 'foo@bar.com'
        form['password'] = 'secret'
        # Submits
        res = form.submit().follow()
        assert res.status_code == 200
        # A new user was created
        assert User.query.count() == old_count + 1
        # Check user can create an event
        view_html = testapp.get('/event/start')
        assert view_html.status_code == 200
        assert '/event/new' in view_html
        

class TestActivation:
    """Activate a user to interact with projects."""

    def test_user_can_activate(self, user, testapp):
        """Create and activate a user."""
        # Make a deactivated user
        user = UserFactory(active=False)
        user.save()
        
        # Let's get an activation mail
        my_hash = user_activation(user)
        # And go activate that user
        res = testapp.get(url_for('auth.activate', userid=user.id, userhash=my_hash))
        assert res.status_code == 302
        assert user.active
        
        # Test the message now
        msg = user_activation_message(user, 'abracadabra')
        assert 'activate' in msg.body

        # Check if the user can be invited by e-mail
        user.email = 'test@dribdat.cc'
        event = EventFactory()
        project = ProjectFactory()
        project.event = event
        project.user = user
        project.save()
        # Mail is not configured in the test environment
        assert user_invitation(user.email, project) is False
        # We can still test the message now
        msg = user_invitation_message(project)
        assert 'invited' in msg.body

    def test_admin_gets_notifcation(self):
        assert False

