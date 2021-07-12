# -*- coding: utf-8 -*-
""" Helper functions for the API """
# Really just a step towards a full API rebuild

import io, csv
from datetime import datetime

from sys import version_info
PY3 = version_info[0] == 3

from dribdat.user.models import Event, Project, Category, Activity
from .aggregation import GetEventUsers

def get_projects_by_event(event_id):
    return Project.query.filter_by(event_id=event_id, is_hidden=False)

def get_event_activities(event_id=None, limit=50, q=None, action=None):
    if event_id is not None:
        event = Event.query.filter_by(id=event_id).first_or_404()
        query = Activity.query \
            .filter(Activity.timestamp>=event.starts_at) \
            .filter(Activity.timestamp<=event.finishes_at)
    else:
        query = Activity.query
    if q is not None:
        q = "%%%s%%" % q
        query = query.filter(Activity.content.like(q))
    if action is not None:
        query = query.filter(Activity.action==action)
    return [a.data for a in query.order_by(Activity.id.desc()).limit(limit).all()]

def get_event_users(event):
    """ Returns plain user objects without personal data """
    userdata = []
    for u in GetEventUsers(event):
        ud = u.data
        userdata.append({
            'id': ud['id'],
            'name': ud['username'],
            'roles': ud['roles'],
            'url': ud['url'],
        })
    return userdata

def get_project_summaries(projects, host_url, is_moar=False):
    if is_moar:
        summaries = []
        for project in projects:
            p = project.data
            p['autotext'] = project.autotext # Markdown
            p['longtext'] = project.longtext # Markdown - see longhtml()
            summaries.append(p)
    else:
        summaries = [ p.data for p in projects ]
    summaries = expand_project_urls(summaries, host_url)
    summaries.sort(key=lambda x: x['score'], reverse=True)
    return summaries

def expand_project_urls(projects, host_url):
    for p in projects:
        p['event_url'] = host_url + p['event_url']
        p['url'] = host_url + p['url']
        p['team'] = ', '.join(p['team'])
    return projects


def gen_rows(csvdata):
    """ Generate rows from data """
    rkrows = []
    headerline = list(csvdata[0].keys())
    rkrows.append(headerline)
    for rk in csvdata:
        rkline = []
        for l in rk.values():
            if l is None:
                rkline.append("")
            elif isinstance(l, (int, float, datetime, str)):
                rkline.append(str(l))
            elif isinstance(l, (dict)):
                rkline.append(json.dumps(l))
            else:
                rkline.append(l.encode('utf-8'))
        rkrows.append(rkline)
    return rkrows


def gen_csv(csvdata):
    """ Generate a CSV file from data rows """
    if len(csvdata) < 1: return ""
    rowdata = gen_rows(csvdata)
    headerline = rowdata[0]
    if PY3:
        output = io.StringIO()
    else:
        output = io.BytesIO()
        headerline = [l.encode('utf-8') for l in headerline]
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(headerline)
    for rk in rowdata[1:]:
        writer.writerow(rk)
    return output.getvalue()
