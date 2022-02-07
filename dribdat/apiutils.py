# -*- coding: utf-8 -*-
""" Helper functions for the API """
# Really just a step towards a full API rebuild

from .aggregation import GetEventUsers
from dribdat.user.models import Event, Project, Category, Activity
import io
import csv
import json
from datetime import datetime

from sys import version_info
PY3 = version_info[0] == 3


def get_projects_by_event(event_id):
    """ Get all the visible projects that belong to an event """
    return Project.query.filter_by(event_id=event_id, is_hidden=False)


def get_event_activities(event_id=None, limit=50, q=None, action=None):
    """ Fetch activities of a given event """
    if event_id is not None:
        event = Event.query.filter_by(id=event_id).first_or_404()
        query = Activity.query \
            .filter(Activity.timestamp >= event.starts_at) \
            .filter(Activity.timestamp <= event.ends_at)
    else:
        query = Activity.query
    if q is not None:
        q = "%%%s%%" % q
        query = query.filter(Activity.content.like(q))
    if action is not None:
        query = query.filter(Activity.action == action)
    results = query.order_by(Activity.id.desc()).limit(limit).all()
    return [a.data for a in results]


def get_event_categories(event_id=None):
    """ Fetch the categories of a given event """
    if event_id is not None:
        event = Event.query.filter_by(id=event_id).first_or_404()
        query = Category.query.filter_by(event_id=event.id)
    else:
        query = Category.query
    return [c.data for c in query.order_by(Category.id.asc()).all()]


def get_event_users(event):
    """ Returns plain user objects without personal data """
    eventusers = GetEventUsers(event)
    if not eventusers:
        return []
    userdata = []
    for u in eventusers:
        ud = u.data
        userdata.append({
            'id': ud['id'],
            'roles': ud['roles'],
            'username': ud['username'],
            'webpage_url': ud['webpage_url'],
        })
    return userdata


def get_project_summaries(projects, host_url, is_moar=False):
    """ Collect data for each project in a list """
    if is_moar:
        summaries = []
        for project in projects:
            p = project.data
            p['autotext'] = project.autotext  # Markdown
            p['longtext'] = project.longtext  # Markdown - see longhtml()
            summaries.append(p)
    else:
        summaries = [p.data for p in projects]
    summaries = expand_project_urls(summaries, host_url)
    summaries.sort(key=lambda x: x['score'], reverse=True)
    return summaries


def get_project_list(event_id, host_url='', full_data=False):
    """ Collect all projects and challenges for an event """
    projects = get_projects_by_event(event_id)
    return get_project_summaries(projects, host_url, full_data)


def expand_project_urls(projects, host_url):
    """ Expand the URLs of projects with that of the host server """
    for p in projects:
        p['event_url'] = host_url + p['event_url']
        p['url'] = host_url + p['url']
        p['team'] = ', '.join(p['team'])
    return projects

def get_schema_for_user_projects(user, host_url):
    """ Generates the metadata for a given user's projects """
    my_projects = user.joined_projects()
    if len(my_projects) == 0:
        return { 'message': "You must join and contribute to at least one project." }
    my_events = {}
    for p in my_projects:
        if p.event_id not in my_events.keys():
            event_data = p.event.get_schema(host_url)
            event_data["workPerformed"] = []
            my_events[p.event_id] = event_data
        my_events[p.event_id]["workPerformed"].append(
            p.get_schema(host_url)
        )
    # Sort in reverse chronological order
    my_schema = [ my_events[e] for e in my_events ]
    my_schema.sort(key=lambda x: x['startDate'], reverse=True)
    return my_schema

def gen_rows(csvdata):
    """ Generate rows from data """
    rkrows = []
    headerline = list(csvdata[0].keys())
    rkrows.append(headerline)
    for rk in csvdata:
        rkline = []
        for line in rk.values():
            if line is None:
                rkline.append("")
            elif isinstance(line, (int, float, datetime, str)):
                rkline.append(str(line))
            elif isinstance(line, (dict)):
                rkline.append(json.dumps(line))
            else:
                rkline.append(line.encode('utf-8'))
        rkrows.append(rkline)
    return rkrows


def gen_csv(csvdata):
    """ Generate a CSV file from data rows """
    if len(csvdata) < 1:
        return ""
    rowdata = gen_rows(csvdata)
    headerline = rowdata[0]
    if PY3:
        output = io.StringIO()
    else:
        output = io.BytesIO()
        headerline = [ln.encode('utf-8') for ln in headerline]
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(headerline)
    for rk in rowdata[1:]:
        writer.writerow(rk)
    return output.getvalue()
