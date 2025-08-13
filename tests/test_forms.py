# -*- coding: utf-8 -*-
"""Test forms."""

from dribdat.user.forms import RegisterForm, LoginForm, ActivationForm, EmailForm
from dribdat.admin.forms import EventForm
from dribdat.user.models import User

from datetime import time, datetime
from dribdat.futures import UTC


class TestRegisterForm:
    """Register form."""

    def test_validate_user_already_registered(self, user):
        """Enter username that is already registered."""
        form = RegisterForm(username=user.username, email='foo@bar.com',
                            password='example', confirm='example')

        assert form.validate() is False
        assert 'A user with this name already exists' in form.username.errors

    def test_validate_email_already_registered(self, user):
        """Enter email that is already registered."""
        form = RegisterForm(username='unique', email=user.email,
                            password='example', confirm='example')

        assert form.validate() is False
        assert 'Email already registered' in form.email.errors

    def test_validate_success(self, db):
        """Register with success."""
        form = RegisterForm(username='newusername', email='new@dribdat.cc',
                            password='example', confirm='example')
        assert form.validate() is True


class TestLoginForm:
    """Login form."""

    def test_validate_success(self, user):
        """Login successful."""
        user.set_password('example')
        user.save()
        form = LoginForm(username=user.username, password='example')
        assert form.validate() is True
        assert form.user == user

    def test_validate_unknown_username(self, db):
        """Unknown username."""
        form = LoginForm(username='unknown', password='example')
        assert form.validate() is False
        assert 'Could not find' in form.username.errors[0]
        assert form.user is None

    def test_validate_invalid_password(self, user):
        """Invalid password."""
        user.set_password('example')
        user.save()
        form = LoginForm(username=user.username, password='wrongpassword')
        assert form.validate() is False
        assert 'Invalid password' in form.password.errors

    def test_validate_inactive_user(self, user, testapp):
        """Inactive user."""
        user.active = False
        user.set_password('example')
        user.save()
        # Correct username and password, but user is not activated
        form = LoginForm(username=user.username, password='example')
        # Deactivated user can still log in
        assert form.validate() is True
        res = testapp.get('/user/%s' % user.username)
        assert 'undergoing review' in res

    def test_activation_form(self, user, testapp):
        """Test the activation of a user."""
        user.active = False
        user.set_hashword('abracadabra')
        user.save()
        form = ActivationForm(code='abracadabra')
        assert form.validate() is True
        # Activate using the GET method
        res = testapp.get('/activate/%d/%s' % (user.id, 'abracadabra'))
        assert res.status_code == 302
        # Check that the user is now active
        user = User.query.get(user.id)
        assert user.active is True

    def test_passwordless_form(self, user, testapp):
        """Test the passwordless login."""
        form = EmailForm(username='abracadabra')
        assert form.validate() is False
        form.username.data = 'abraca@dabra.org'
        assert form.validate() is True
        # Try the passwordless login (just a redirect)
        res = testapp.post('/passwordless/', params={'username': user.email})
        assert res.status_code == 302

    def test_user_deletion(self, user, testapp):
        """Test the deactivation of a user."""
        # Log in with the user
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'myprecious'
        res = form.submit().follow()
        assert res.status_code == 200
        # Delete using the GET method
        res = testapp.post('/user/profile/delete')
        assert res.status_code == 302
        # Check that the user is now gone
        user = User.query.get(user.id)
        assert user is None



class TestEventForm:
    """Event entry form."""

    def test_create_new_event(self, event):
        """Sample event."""
        form = EventForm()
        # A name is required
        assert form.validate() is False
        assert 'This field is required.' in form.name.errors
        form = EventForm(name="test")
        assert form.validate() is True

    def test_event_validate_time(self, event):
        """Time validation test."""
        form = EventForm(
            event_id=event.id, name="Name",
            starts_date=datetime.now(UTC), ends_date=datetime.now(UTC),
            starts_time=time(2, 0, 0), ends_time=time(1, 0, 0))
        # Ends before starting
        # assert form.validate() is False
        # assert 'Start time must be before end time.'
        # in form.starts_time.errors
        # TODO: fixme
        assert form.validate() is True
