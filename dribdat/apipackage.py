# -*- coding: utf-8 -*-
""" Importing event data from a package """

import logging
import requests
from datetime import datetime as dt
from .user.models import Event, Project, Activity, Category, User, Role


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
        user = User.query.filter_by(username=name).first()
        if user:
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
    for act in data:
        aname = act['name']
        tstamp = dt.utcfromtimestamp(act['time'])
        activity = Activity.query.filter_by(name=aname,
                                            timestamp=tstamp).first()
        if activity:
            continue
        logging.info('Creating activity', tstamp)
        pname = act['project_name']
        proj = Project.query.filter_by(name=pname).first()
        if not proj:
            logging.warn('Error! Project not found: %s' % pname)
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
    # Initial import
    for res in data['resources']:
        if res['name'] == 'events':
            updates['events'] = importEvents(res['data'], DRY_RUN)

        elif res['name'] == 'categories' and ALL_DATA:
            updates['categories'] = importCategories(res['data'], DRY_RUN)

        elif res['name'] == 'users' and ALL_DATA:
            updates['users'] = importUsers(res['data'], DRY_RUN)
    # Projects follow users
    for res in data['resources']:
        if res['name'] == 'projects' and ALL_DATA:
            updates['projects'] = importProjects(res['data'], DRY_RUN)
    # Activities always last
    for res in data['resources']:
        if res['name'] == 'activities' and ALL_DATA:
            updates['activities'] = importActivities(res['data'], DRY_RUN)
    # Return summary object
    return updates


def ImportEventByURL(url, DRY_RUN=False, ALL_DATA=False):
    try:
        data = requests.get(url)
    except requests.exceptions.RequestException:
        logging.error("Could not connect to %s" % url)
        return {}
    return ImportEventPackage(data.json(), DRY_RUN, ALL_DATA)
