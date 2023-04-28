#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Management functions for dribdat."""
import os
import click
import datetime as dt
from dribdat.app import init_app
from dribdat.settings import DevConfig, ProdConfig
from dribdat.apipackage import fetch_datapackage, load_file_datapackage

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')


def create_app(script_info=None):
    """Initialise the app object."""
    if os.environ.get("DRIBDAT_ENV") == 'prod':
        app = init_app(ProdConfig)
    else:
        app = init_app(DevConfig)
    return app


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
@click.argument('event', required=True)
@click.argument('clear', required=False, default=False)
@click.argument('primes', required=False, default=True)
@click.argument('challenges', required=False, default=True)
def numerise(event: int, clear: bool, primes: bool, challenges: bool):
    """Assign numbers to challenge hashtags for an EVENT ID."""
    if clear:
        print("- Clearing hashtags")
    if primes:
        print("- Using prime numbers")
    if challenges:
        print("- Only challenges")
    else:
        print("- Only projects")
    # TODO: use a parameter for sort order alphabetic, id-based, etc.
    if primes:
        # Generate some primes, thanks @DhanushNayak
        nq = list(filter(lambda x: not list(filter(lambda y : x%y==0, range(2,x))), range(2,200)))
    else:
        nq = list(range(1,200))
    with create_app().app_context():
        from dribdat.user.models import Event, Project
        event = Event.query.filter_by(id=event).first_or_404()
        print("Applying numbers to event: ", event.name)
        projects = Project.query.filter_by(event_id=event.id) \
                    .order_by(Project.progress.desc()) \
                    .order_by(Project.name)
        ix = 0
        for c in projects:
            if c.is_hidden: continue
            if challenges and not c.is_challenge: continue
            if not challenges and c.is_challenge: continue
            ch = "" # push existing hashtag aside
            if not clear and len(c.hashtag) > 0:
                ch = " " + ch
            c.hashtag = str(nq[ix]) + ch
            c.save()
            ix = ix + 1
        print("Enumerated %d projects." % projects.count())


@click.command()
@click.argument('name', required=True)
@click.argument('start', required=False)
@click.argument('finish', required=False)
def event_start(name, start=None, finish=None):
    """Create a new event."""
    if start is None:
        start = dt.datetime.now() + dt.timedelta(days=1)
    else:
        start = dt.datetime.parse(start)
    if finish is None:
        finish = dt.datetime.now() + dt.timedelta(days=2)
    else:
        finish = dt.datetime.parse(finish)
    with create_app().app_context():
        from dribdat.user.models import Event
        event = Event(name=name, starts_at=start, ends_at=finish)
        event.save()
        print("Created event %d" % event.id)


@click.command()
@click.argument('url', required=True)
@click.argument('level', required=False)
def imports(url, level='full'):
    """Import a new event from a URI or file."""
    # Configuration
    dry_run = True
    all_data = False
    if level == 'basic':
        dry_run = False
    elif level == 'full':
        dry_run = False
        all_data = True
    else:
        level = 'dry run'
    print("Starting %s import" % level)
    with create_app().app_context():
        if url.startswith('http'):
            results = fetch_datapackage(url, dry_run, all_data)
        else:
            results = load_file_datapackage(url, dry_run, all_data)
    event_names = ', '.join([r['name'] for r in results['events']])
    if 'errors' in results:
        print(results['errors'])
    else:
        print("Created events: %s" % event_names)


@click.command()
@click.argument('kind', nargs=-1, required=False)
def exports(kind):
    """Export some data."""
    with create_app().app_context():
        if 'people' in kind:
            from dribdat.user.models import User
            for pp in User.query.filter_by(active=True).all():
                print(pp.email)
        elif 'events' in kind:
            from dribdat.user.models import Event
            for pp in Event.query.filter_by(is_hidden=False).all():
                print('\t'.join([pp.name, str(pp.starts_at), str(pp.ends_at)]))


@click.group(name='j')
def cli():
    """dribdat command line interfoot."""
    pass


cli.add_command(socialize)
cli.add_command(numerise)
cli.add_command(imports)
cli.add_command(exports)

if __name__ == '__main__':
    cli()
