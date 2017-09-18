#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask.cli import FlaskGroup
from flask_migrate import MigrateCommand

from dribdat.app import init_app
from dribdat.user.models import User
from dribdat.settings import DevConfig, ProdConfig
from dribdat.database import db

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

def shell_context():
    """Return context dict for a shell session"""
    return {'app': app, 'db': db, 'User': User}

def create_app(script_info=None):
    """Initialise the app object"""
    if os.environ.get("DRIBDAT_ENV") == 'prod':
        app = init_app(ProdConfig)
    else:
        app = init_app(DevConfig)
    app.shell_context_processor(shell_context)
    return app

cli = FlaskGroup(create_app=create_app)

@cli.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code

cli.add_command('db', MigrateCommand)

if __name__ == '__main__':
    cli()
