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
    # Start Dribdat in dev mode by default
    if os.environ.get("DRIBDAT_ENV", "dev") == 'prod':
        app = init_app(ProdConfig)
        print("Dribdat is production ready")
    else:
        app = init_app(DevConfig)
        print("Dribdat in development mode")
    # Helpful info for maintainers
    print(" * Database: " + app.config['SQLALCHEMY_DATABASE_URI'].split(':/')[0])
    # Enable debugger and profiler
    if bool(strtobool(os.environ.get("FLASK_DEBUG", "False"))):
        app.debug = True
        # You can still enable the profiler manually in the toolbar
        app.config['DEBUG_TB_PROFILER_ENABLED'] = False
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)
    # Pass through shell commands
    app.shell_context_processor(shell_context)
    return app


def testrunner(name, warnings=None):
    """Runs the name with warnings"""
    if len(name):
        feat_test = os.path.join(TEST_PATH, "test_%s.py" % name)
    else:
        feat_test = TEST_PATH
    import subprocess
    if warnings is None:
        return subprocess.call(['pytest', feat_test])
    return subprocess.call(['pytest', warnings, feat_test])


@click.command()
@click.argument('name', nargs=-1, required=False)
def test(name):
    """Run all or just a subset of tests."""
    """Parameter: which test set to run (features, functional, ..)"""
    return testrunner(name)


@click.command()
@click.argument('name', nargs=-1, required=False)
def testwarn(name):
    """Run all or just a subset of tests with warnings."""
    return testrunner(name, "-W default")


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Script for managing this application."""
    pass


cli.add_command(test)

if __name__ == '__main__':
    cli()
