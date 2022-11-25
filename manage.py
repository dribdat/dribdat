#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Management functions for dribdat."""
import os
import click
from flask.cli import FlaskGroup
from dribdat.app import init_app
from dribdat.utils import strtobool
from dribdat.settings import DevConfig, ProdConfig

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')


def shell_context():
    """Return context dict for a shell session."""
    from dribdat.user.models import User, Event, Project, Category, Activity
    return {
        'User': User, 'Event': Event, 'Project': Project,
        'Category': Category, 'Activity': Activity
    }


def create_app(script_info=None):
    """Initialise the app object."""
    if os.environ.get("DRIBDAT_ENV") == 'prod':
        app = init_app(ProdConfig)
    else:
        app = init_app(DevConfig)
    # Enable debugger and profiler
    if bool(strtobool(os.environ.get("FLASK_DEBUG", "False"))):
        app.config['DEBUG_TB_PROFILER_ENABLED'] = True
        app.debug = True
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)
        # from werkzeug.middleware.profiler import ProfilerMiddleware
        # app.wsgi_app = ProfilerMiddleware(
        #     app.wsgi_app,
        #     restrictions=[5, 'public'],
        #     profile_dir='./profile',
        # )
    # Pass through shell commands
    app.shell_context_processor(shell_context)
    return app


@click.command()
@click.argument('name', nargs=-1, required=False)
def test(name):
    """Run all or just a subset of tests."""
    """Parameter: which test set to run (features, functional, ..)"""
    if len(name):
        feat_test = os.path.join(TEST_PATH, "test_%s.py" % name)
    else:
        feat_test = TEST_PATH
    import subprocess
    return subprocess.call(['pytest', feat_test])


@click.command()
@click.argument('kind', nargs=-1, required=False)
def socialize(kind):
    """Reset user profile data."""
    """Parameter: which models to refresh (users, ..)"""
    with create_app().app_context():
        # TODO: use the kind parameter to refresh projects, etc.
        from dribdat.user.models import User
        q = [u.socialize() for u in User.query.all()]
        print("Updated %d users." % len(q))


@click.command()
@click.argument('name', required=True)
@click.argument('start', required=False)
def event_start(name, start=None):
    """Create a new event."""
    if start is None:
        start = dt.datetime.now() + dt.timedelta(days=1)
    else:
        start = parse(start)
    event = Event(name="test", starts_at=start)
    event.save()
    print("Created event %d" % event.id)


@click.command()
@click.argument('kind', nargs=-1, required=False)
def exports(kind):
    """Export some data."""
    with create_app().app_context():
        if 'people' in kind:
            from dribdat.user.models import User
            for pp in User.query.all():
                print(pp.email)


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Script for managing this application."""
    pass


cli.add_command(test)
cli.add_command(socialize)
cli.add_command(exports)

if __name__ == '__main__':
    cli()
