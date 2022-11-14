# -*- coding: utf-8 -*-
""" Importing event data from a package """

import logging
import requests
from datetime import datetime as dt
from frictionless import Package, Resource
from .user.models import Event, Project, Activity, Category, User, Role
from .utils import format_date
from .apiutils import (
    get_project_list,
    get_event_users,
    get_event_activities,
    get_event_categories,
)

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10


def PackageEvent(event, author=None, host_url='', full_contents=False):
    """ Creates a Data Package from the data of an event """

    # Define the author, if available
    contributors = []
    if author and not author.is_anonymous:
        contributors.append({
            "title": author.username,
            "path": author.webpage_url or '',
            "role": "author"
        })
    else:
        # Disallow anon access to full data
        full_contents = False

    # Set up a data package object
    package = Package(
        name='event-%d' % event.id,
        title=event.name,
        description=event.summary or event.description,
        keywords=["dribdat", "hackathon", "co-creation"],
        sources=[{"title": "dribdat", "path": "https://dribdat.cc"}],
        licenses=[{
            "name": "ODC-PDDL-1.0",
            "path": "http://opendatacommons.org/licenses/pddl/",
            "title": "Open Data Commons Public Domain Dedication & License 1.0"
        }],
        contributors=contributors,
        homepage=event.webpage_url or '',
        created=format_date(dt.now(), '%Y-%m-%dT%H:%M'),
        version="0.2.0",
    )

    # if False:  # as CSV
    #     fp_projects = tempfile.NamedTemporaryFile(
    #         mode='w+t', prefix='projects-', suffix='.csv')
    #     # print("Writing to temp CSV file", fp_projects.name)
    #     fp_projects.write(gen_csv(get_project_list(event.id)))
    #     resource = Resource(fp_projects.name)
    # if False:
    #     # print("Generating in-memory rowset")
    #     project_rows = gen_rows(get_project_list(event.id))
    #     resource = Resource(
    #         name='projects',
    #         data=project_rows,
    #     )

    # Generate resources

    # print("Generating in-memory JSON of event")
    package.add_resource(Resource(
            name='events',
            data=[event.get_full_data()],
        ))
    # print("Generating in-memory JSON of projects")
    package.add_resource(Resource(
            name='projects',
            data=get_project_list(event.id, host_url, True),
        ))
    if full_contents:
        # print("Generating in-memory JSON of participants")
        package.add_resource(Resource(
                name='users',
                data=get_event_users(event, full_contents),
            ))
        # print("Generating in-memory JSON of activities")
        package.add_resource(Resource(
                name='activities',
                data=get_event_activities(event.id, 500),
            ))
        # print("Generating in-memory JSON of activities")
        package.add_resource(Resource(
                name='categories',
                data=get_event_categories(event.id),
            ))
        # print("Adding supplementary README")
        package.add_resource(Resource(
                name='readme',
                path='PACKAGE.txt',
            ))

    return package


def importEvents(data, DRY_RUN=False):
    updates = []
    for evt in data:
        name = evt['name']
        event = Event.query.filter_by(name=name).first()
        if not event:
            logging.info('Creating event: %s' % name)
            event = Event()
        else:
            logging.info('Updating event: %s' % name)
        event.set_from_data(evt)
        if not DRY_RUN:
            event.save()
        updates.append(event.data)
    return updates


def importCategories(data, DRY_RUN=False):
    updates = []
    for ctg in data:
        name = ctg['name']
        category = Category.query.filter_by(name=name).first()
        if not category:
            logging.info('Creating category: %s' % name)
            category = Category()
        else:
            logging.info('Updating category: %s' % name)
        category.set_from_data(ctg)
        if not DRY_RUN:
            category.save()
        updates.append(category.data)
    return updates


def importUsers(data, DRY_RUN=False):
    updates = []
    for usr in data:
        name = usr['username']
        if name is None or len(name) < 4:
            continue
        email = usr['email'] if 'email' in usr else ''
        if User.query.filter_by(username=name).first() or \
           User.query.filter_by(email=email).first():
            # Do not update existing user data
            logging.info('Skipping user: %s' % name)
            continue
        logging.info('Creating user: %s' % name)
        user = User()
        user.set_from_data(usr)
        importUserRoles(user, usr['roles'], DRY_RUN)
        if not DRY_RUN:
            user.save()
        updates.append(user.data)
    return updates


def importUserRoles(user, new_roles, DRY_RUN=False):
    updates = []
    my_roles = [r.name for r in user.roles]
    for r in new_roles.split(','):
        if r in my_roles:
            continue
        # Check that role is a new one
        role = Role.query.filter_by(name=r).first()
        if not role:
            role = Role(r)
            if DRY_RUN:
                continue
            role.save()
        user.roles.append(role)
        updates.append(role.name)
    return updates


def importProjects(data, DRY_RUN=False):
    updates = []
    for pjt in data:
        name = pjt['name']
        project = Project.query.filter_by(name=name).first()
        if not project:
            logging.info('Creating project: %s' % name)
            project = Project()
        else:
            logging.info('Updating project: %s' % name)
        project.set_from_data(pjt)
        # Search for event
        event_name = pjt['event_name']
        event = Event.query.filter_by(name=event_name).first()
        if not event:
            logging.warn('Error - event not found: %s' % event_name)
            continue
        project.event = event
        if not DRY_RUN:
            project.save()
        updates.append(project.data)
    return updates


def importActivities(data, DRY_RUN=False):
    updates = []
    proj = None
    pname = ""
    for act in data:
        aname = act['name']
        tstamp = dt.utcfromtimestamp(act['time'])
        activity = Activity.query.filter_by(name=aname,
                                            timestamp=tstamp).first()
        if activity:
            logging.info('Skipping activity', tstamp)
            continue
        logging.info('Creating activity', tstamp)
        if act['project_name'] != pname:
            pname = act['project_name']
            # TODO: unreliable; rather use a map of project_id to new id
            proj = Project.query.filter_by(name=pname).first()
        if not proj:
            logging.warn('Error! Project not found: %s' % pname)
            continue
        activity = Activity(aname, proj.id)
        activity.set_from_data(act)
        if not DRY_RUN:
            activity.save()
        updates.append(activity.data)
    return updates


def ImportEventPackage(data, DRY_RUN=False, ALL_DATA=False):
    if 'sources' not in data or data['sources'][0]['title'] != 'dribdat':
        return {'errors': ['Invalid source']}
    updates = {}
    # Import in stages
    for stg in [1, 2, 3]:
        for res in data['resources']:
            # Import events
            if stg == 1 and res['name'] == 'events':
                updates['events'] = importEvents(res['data'], DRY_RUN)
            # Import categories
            elif stg == 1 and res['name'] == 'categories' and ALL_DATA:
                updates['categories'] = importCategories(res['data'], DRY_RUN)
            # Import user accounts
            elif stg == 1 and res['name'] == 'users' and ALL_DATA:
                updates['users'] = importUsers(res['data'], DRY_RUN)
            # Projects follow users
            if stg == 2 and res['name'] == 'projects' and ALL_DATA:
                updates['projects'] = importProjects(res['data'], DRY_RUN)
            # Activities always last
            if stg == 3 and res['name'] == 'activities' and ALL_DATA:
                updates['activities'] = importActivities(res['data'], DRY_RUN)
    # Return summary object
    return updates


def ImportEventByURL(url, DRY_RUN=False, ALL_DATA=False):
    try:
        data = requests.get(url, timeout=REQUEST_TIMEOUT).json()
    except requests.exceptions.RequestException:
        logging.error("Could not connect to %s" % url)
        return {}
    return ImportEventPackage(data, DRY_RUN, ALL_DATA)
