#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Management functions for dribdat."""
import os
import click
from flask.cli import FlaskGroup

from dribdat.app import init_app
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
def socialize():
    """Reset user profile data."""
    with create_app().app_context():
        from dribdat.user.models import User
        q = [u.socialize() for u in User.query.all()]
        print("Updated %d users." % len(q))


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Script for managing this application."""
    pass


cli.add_command(test)
cli.add_command(socialize)

if __name__ == '__main__':
    cli()
