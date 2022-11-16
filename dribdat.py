#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shell access to dribdat."""
import os
import click
import datetime as dt
from flask.cli import AppGroup
from dateutil.parser import parse
from dribdat.app import init_app
from dribdat.settings import DevConfig, ProdConfig
from dribdat.user.models import Event
from flask.helpers import get_debug_flag

CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = init_app(CONFIG)

event_cli = AppGroup('event')


@event_cli.command('start')
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


app.cli.add_command(event_start())
