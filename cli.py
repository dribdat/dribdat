#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Management functions for dribdat."""
import os
import time
import click
from datetime import datetime, timedelta
from dribdat.app import init_app
from dribdat.user.models import User, Event
from dribdat.settings import DevConfig, ProdConfig
from dribdat.apipackage import fetch_datapackage, load_file_datapackage, import_users_csv
from dribdat.futures import UTC

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
def ls():
    """Lists events here."""
    from dribdat.user.models import Event
    q = Event.query.filter_by(is_hidden=False).order_by(Event.starts_at.desc())
    print('total %d' % q.count())
    for e in q.all():
        print('%d\t%s\t%d' % (e.id, e.name, e.project_count))


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
@click.argument('primes', required=False, default=False)
@click.argument('challenges', required=False, default=False)
def numerise(event: int, clear: bool, primes: bool, challenges: bool):
    """Assign numbers to project or challenge identifiers for a given EVENT ID."""
    if clear:
        print("- Clear idents rather than set them")
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
        projects = Project.query \
                    .filter_by(event_id=event.id, is_hidden=False) \
                    .filter(Project.progress >= 0) \
                    .order_by(Project.id)
        ix = 0
        count = projects.count()
        for c in projects:
            if c.is_hidden: continue
            if challenges and not c.is_challenge: continue
            if not challenges and c.is_challenge: continue
            if clear:
                c.ident = ''
            else:
                prefix = ''
                if count > 99 and nq[ix] < 100:
                    prefix = prefix + '0'
                if count > 9 and nq[ix] < 10:
                    prefix = prefix + '0'
                c.ident = prefix + str(nq[ix])
            c.save()
            ix = ix + 1
        print("Enumerated %d projects." % ix)


@click.command()
@click.argument('name', required=True)
@click.argument('start', required=False)
@click.argument('finish', required=False)
def event_start(name, start=None, finish=None):
    """Create a new event."""
    if start is None:
        start = datetime.now(UTC) + timedelta(days=1)
    else:
        start = datetime.parse(start)
    if finish is None:
        finish = datetime.now(UTC) + timedelta(days=2)
    else:
        finish = datetime.parse(finish)
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
@click.argument('kind', nargs=-1, required=False, help="people or events")
def exports(kind):
    """Export system data to CSV."""
    with create_app().app_context():
        if 'people' in kind:
            print(';'.join(['username','email','updated_at','fullname']))
            for pp in User.query.filter_by(active=True).all():
                print(';'.join([pp.username, pp.email, str(pp.updated_at or ''), str(pp.fullname or '').replace(';',':')]))
        elif 'events' in kind:
            print(';'.join(['name','starts_at','ends_at']))
            for pp in Event.query.filter_by(is_hidden=False).all():
                print(';'.join([pp.name.replace(';',':'), str(pp.starts_at), str(pp.ends_at)]))
        else:
            print('At least one <kind> should be provided. See --help')


@click.command()
@click.argument('filename', required=True)
@click.argument('testonly', required=False)
def register(filename, testonly=False):
    """Import user data from a CSV file."""
    with create_app().app_context():
        created, updated = import_users_csv(filename, testonly)
        print('%d users imported, %d were updated')


@click.command()
@click.option('-0', '--lowscore', is_flag=True, help="Users with a low score")
@click.option('-i', '--inactive', is_flag=True, help="Users which are not active")
@click.option('-o', '--withsso', is_flag=True, help="Include users with active SSO")
@click.option('-d', '--delete', is_flag=True, help="Delete users, not just deactivate them")
@click.option('-s', '--score', required=False, default=0, help="What counts as a minimum low score")
def kick(lowscore: bool, inactive: bool, withsso: bool, delete: bool, score: int):
    """Cull inactive accounts on the system."""
    with create_app().app_context():
        q_active = User.query.filter_by(active=True, is_admin=False)
        q_inactive = User.query.filter_by(active=False, is_admin=False)
        print('There are currently %d active and %d blocked user accounts.' % (q_active.count(), q_inactive.count()))
        
        whatnext = 'blocked'
        if delete:
            whatnext = 'deleted'
        if inactive and lowscore:
            print('All inactive users with no content will be %s.' % whatnext)
        elif inactive:
            print('All inactive users are about to be %s.' % whatnext)
        elif lowscore:
            print('Any users with no content are about to be %s.' % whatnext)
        else:
            print('You need to specify a condition to kick users.')
            return

        delcount = 0
        del_targets = []
        if inactive: 
            del_query = q_inactive.all()
        else:
            del_query = q_active.all()
        for u in del_query:
            if withsso or not u.sso_id:
                if not lowscore:
                    del_targets.append(u)
                elif not u.posted_challenges() and not u.joined_projects() and u.get_score() < score:
                    del_targets.append(u)

        if len(del_targets) > 0:
            print('This will affect a total of %d users' % len(del_targets))
            print('... waiting 5 seconds - Ctrl-C to abort! ...')
            time.sleep(5)

            print('---------------------------------------------------------------')
            print('username,fullname,email,webpage_url')
            for u in del_targets:
                if delete:
                    u.delete()
                else:
                    u.active = False
                    u.save()
                print(','.join([u.username, u.fullname or '', u.email, u.webpage_url or '']))
                delcount = delcount + 1
            print('---------------------------------------------------------------')

        print('%d user accounts cleaned up' % delcount)


@click.group(name='j')
def cli():
    """dribdat command line interfoot."""
    pass


cli.add_command(socialize)
cli.add_command(numerise)
cli.add_command(register)
cli.add_command(imports)
cli.add_command(exports)
cli.add_command(kick)

if __name__ == '__main__':
    cli()
