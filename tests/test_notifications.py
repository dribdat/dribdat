# -*- coding: utf-8 -*-
"""Functional tests for admin notifications."""
from flask import url_for
from dribdat.user.models import Event, Project

class TestAdminNotifications:
    """Admin notifications."""

    def test_notify_admin_on_event_creation(self, user, testapp):
        """Test that admin is notified when a new event is created."""
        user.is_admin = False
        user.set_password('password')
        user.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'password'
        res = form.submit().follow()

        # Enable events in config for testing
        testapp.app.config['DRIBDAT_ALLOW_EVENTS'] = True
        testapp.app.config['MAIL_NOTIFY_ADMIN'] = 'admin@example.com'
        testapp.app.config['MAIL_SERVER'] = 'localhost' # Needed to initialize mailman
        testapp.app.testing = True

        # Initialize mailman manually for testing since it wasn't initialized in TestConfig
        from flask_mailman import Mail
        mail = Mail()
        mail.init_app(testapp.app)

        # Ensure we use locmem backend and clear outbox
        testapp.app.extensions['mailman'].outbox = []

        # Go to new event page
        res = testapp.get(url_for('public.event_new'))
        form = res.forms[0]
        form['name'] = 'New Shiny Event'

        res = form.submit().follow()
        assert res.status_code == 200
        assert Event.query.filter_by(name='New Shiny Event').first() is not None

        # Check if notification was sent
        outbox = testapp.app.extensions['mailman'].outbox
        assert len(outbox) > 0
        assert any('A new event' in m.body for m in outbox)
        assert any('admin@example.com' in m.to for m in outbox)

    def test_notify_admin_on_project_creation(self, user, testapp):
        """Test that admin is notified when a new project is created."""
        user.is_admin = False
        user.set_password('password')
        user.save()

        # Create an event
        from .factories import EventFactory
        event = EventFactory()
        event.lock_resources = False # Not a bootstrap event
        event.save()

        # Login
        res = testapp.get('/login/')
        form = res.forms['loginForm']
        form['username'] = user.username
        form['password'] = 'password'
        res = form.submit().follow()

        testapp.app.config['MAIL_NOTIFY_ADMIN'] = 'admin@example.com'
        testapp.app.config['MAIL_SERVER'] = 'localhost' # Needed to initialize mailman
        testapp.app.testing = True

        # Initialize mailman manually for testing since it wasn't initialized in TestConfig
        from flask_mailman import Mail
        mail = Mail()
        mail.init_app(testapp.app)

        # Ensure we use locmem backend and clear outbox
        testapp.app.extensions['mailman'].outbox = []

        # Go to new project page
        res = testapp.get(url_for('project.project_new', event_id=event.id))
        form = res.forms['projectNew']
        form['name'] = 'New Shiny Project'

        res = form.submit().follow()
        assert res.status_code == 200
        assert Project.query.filter_by(name='New Shiny Project').first() is not None

        # Check if notification was sent
        outbox = testapp.app.extensions['mailman'].outbox
        assert len(outbox) > 0
        assert any('A new project' in m.body for m in outbox)
        assert any('admin@example.com' in m.to for m in outbox)
