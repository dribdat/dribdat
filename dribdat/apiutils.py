# -*- coding: utf-8 -*-
"""Helper functions for the API."""
# Really just a step towards a full API rebuild

import io
import csv
import json

from datetime import datetime

from dribdat.user.models import Event, Project, Category, Activity
from dribdat.utils import format_date
from .aggregation import GetEventUsers

from sys import version_info
PY3 = version_info[0] == 3


def get_projects_by_event(event_id):
    """Get all the visible projects that belong to an event."""
    return Project.query \
        .filter_by(event_id=event_id, is_hidden=False) \
        .filter(Project.progress >= 0) \
        .order_by(Project.progress.desc()) \
        .order_by(Project.name)


def get_event_activities(event_id=None, limit=50, q=None, action=None):
    """Fetch activities of a given event."""
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
    """Fetch the categories of a given event."""
    if event_id is not None:
        event = Event.query.filter_by(id=event_id).first_or_404()
        query = Category.query.filter_by(event_id=event.id)
    else:
        query = Category.query
    return [c.data for c in query.order_by(Category.id.asc()).all()]


def get_event_users(event, full_data=False):
    """Return plain formatted user objects and personal data."""
    eventusers = GetEventUsers(event)
    if not eventusers:
        return []
    userdata = []
    for u in eventusers:
        if full_data:
            usr = u.data
        else:
            usr = {
                'id': u.data['id'],
                'roles': u.data['roles'],
                'username': u.data['username'],
                'webpage_url': u.data['webpage_url'],
            }
        if 'created_at' in usr and usr['created_at']:
            usr['created_at'] = format_date(
                usr['created_at'])
        if 'updated_at' in usr and usr['updated_at']:
            usr['updated_at'] = format_date(
                usr['updated_at'])
        userdata.append(usr)
    return userdata


# TODO: combine with function above
def get_users_for_event(event=None, with_score=False):
    """Collect full user data for a particular event, optionally with the user scores."""
    if event is None: return []
    userlist = []
    for u in GetEventUsers(event):
         # with_challenges=True, limit=-1, event=None
        udata = u.data
        pnames = [ p.name for p in u.joined_projects(True, -1, event) ]
        udata['teams'] = ', '.join(pnames)
        if with_score:
            udata['score'] = u.get_score()
        userlist.append(udata)
    return userlist


def get_project_summaries(projects, host_url, is_moar=False):
    """Collect data for each project in a list."""
    summaries = []
    for project in projects:
        p = project.data
        if is_moar:
            p['stats'] = project.get_stats()
            p['autotext'] = project.autotext  # Markdown
            p['longtext'] = project.longtext  # Markdown - see longhtml()
        else:
            stats = project.get_stats()
            for k in stats.keys():
                p['stats-' + k] = stats[k]
        summaries.append(p)
    summaries = expand_project_urls(summaries, host_url)
    summaries.sort(key=lambda x: x['score'] or 0, reverse=True)
    return summaries


def get_project_list(event_id, host_url='', full_data=False):
    """Collect all projects and challenges for an event."""
    projects = get_projects_by_event(event_id)
    return get_project_summaries(projects, host_url, full_data)


def expand_project_urls(projects, host_url):
    """Expand the URLs of projects with that of the host server."""
    for p in projects:
        p['event_url'] = host_url + p['event_url']
        p['url'] = host_url + p['url']
        p['team'] = ', '.join(p['team'])
    return projects


def get_schema_for_user_projects(user, host_url):
    """Generate the metadata for a given user's projects."""
    my_projects = user.joined_projects()
    if len(my_projects) == 0:
        return {'message': "Please join and contribute to at least 1 project."}
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
    my_schema = [my_events[e] for e in my_events]
    my_schema.sort(key=lambda x: x['startDate'], reverse=True)
    return my_schema


def gen_rows(csvdata):
    """Generate rows from data."""
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
    """Generate a CSV file from data rows."""
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


def event_upload_configuration(import_level='test'):
    """Configure the upload."""
    dry_run = True
    all_data = False
    if import_level == 'basic':
        dry_run = False
        status = "Basic"
    elif import_level == 'full':
        dry_run = False
        all_data = True
        status = "Complete"
    else:
        status = "Preview"
    return dry_run, all_data, status
