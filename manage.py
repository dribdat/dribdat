#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import click

from flask import Flask
from flask.cli import FlaskGroup
from flask_migrate import MigrateCommand

from dribdat.app import init_app
from dribdat.settings import DevConfig, ProdConfig
from dribdat.database import db

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

def shell_context():
    """Return context dict for a shell session"""
    from dribdat.user.models import User, Event, Project, Category, Activity
    return {'User': User, 'Event':Event, 'Project':Project, 'Category':Category, 'Activity':Activity}

def create_app(script_info=None):
    """Initialise the app object"""
    if os.environ.get("DRIBDAT_ENV") == 'prod':
        app = init_app(ProdConfig)
    else:
        app = init_app(DevConfig)
    app.shell_context_processor(shell_context)
    app.cli.add_command('db', MigrateCommand)
    return app

@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is a management script for the wiki application."""

@click.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code

if __name__ == '__main__':
    cli()
