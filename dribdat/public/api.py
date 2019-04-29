# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, make_response, request, flash, jsonify, current_app
from flask_login import login_required, current_user

from sqlalchemy import or_

from ..extensions import db
from ..utils import timesince

from ..user.models import Event, Project, Category, Activity
from ..aggregation import GetProjectData, GetProjectTeam

from datetime import datetime
from flask import Response, stream_with_context
import io, csv, json, sys
PY3 = sys.version_info[0] == 3

blueprint = Blueprint('api', __name__, url_prefix='/api')

def get_projects_by_event(event_id):
    return Project.query.filter_by(event_id=event_id, is_hidden=False)

def get_project_summaries(projects):
    summaries = [ p.data for p in projects ]
    summaries.sort(key=lambda x: x['score'], reverse=True)
    return summaries

# Collect all projects for an event
def project_list(event_id):
    projects = get_projects_by_event(event_id).filter(Project.progress >= 0)
    return get_project_summaries(projects)

# Collect all challenges for an event
def challenges_list(event_id):
    projects = get_projects_by_event(event_id).filter(Project.progress < 0)
    return get_project_summaries(projects)

# Generate a CSV file
def gen_csv(csvdata):
    headerline = csvdata[0].keys()
    if PY3:
        output = io.StringIO()
    else:
        output = io.BytesIO()
        headerline = [l.encode('utf-8') for l in headerline]
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(headerline)
    for rk in csvdata:
        rkline = []
        for l in rk.values():
            if l is None:
                rkline.append("")
            elif isinstance(l, (int, float, datetime)):
                rkline.append(l)
            else:
                rkline.append(l.encode('utf-8'))
        writer.writerow(rkline)
    return output.getvalue()

# ------ EVENT INFORMATION ---------

# API: Outputs JSON about the current event
@blueprint.route('/event/current/info.json')
def info_current_event_json():
    event = Event.query.filter_by(is_current=True).first()
    return jsonify(event=event.data, timeuntil=timesince(event.countdown, until=True))

# API: Outputs JSON about an event
@blueprint.route('/event/<int:event_id>/info.json')
def info_event_json(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(event=event.data, timeuntil=timesince(event.countdown, until=True))

# API: Outputs JSON-LD about an Event according to https://schema.org/Event specification
@blueprint.route('/event/<int:event_id>/hackathon.json')
def info_event_hackathon_json(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(event.get_schema(request.host_url))

# ------ EVENT PROJECTS ---------

# API: Outputs JSON of projects in the current event, along with its info
@blueprint.route('/event/current/projects.json')
def project_list_current_json():
    event = Event.query.filter_by(is_current=True).first()
    return jsonify(projects=project_list(event.id), event=event.data)

# API: Outputs JSON of all projects at a specific event
@blueprint.route('/event/<int:event_id>/projects.json')
def project_list_json(event_id):
    return jsonify(projects=project_list(event_id))

# API: Outputs CSV of all projects in an event
@blueprint.route('/event/<int:event_id>/projects.csv')
def project_list_csv(event_id):
    return Response(stream_with_context(gen_csv(project_list(event_id))),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=project_list.csv'})

# API: Outputs JSON of ideas/challenges in the current event, along with its info
@blueprint.route('/event/current/challenges.json')
def challenges_list_current_json():
    event = Event.query.filter_by(is_current=True).first()
    return jsonify(challenges=challenges_list(event.id), event=event.data)

# API: Outputs JSON of categories in the current event
@blueprint.route('/event/current/categories.json')
def categories_list_current_json():
    event = Event.query.filter_by(is_current=True).first()
    return jsonify(categories=[ c.data for c in event.categories_for_event() ], event=event.data)

# ------ ACTIVITY FEEDS ---------

def get_event_activities(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return [a.data for a in Activity.query
              .filter(Activity.timestamp>=event.starts_at)
              .order_by(Activity.id.desc()).all()]

# API: Outputs JSON of recent activity in an event
@blueprint.route('/event/<int:event_id>/activity.json')
def event_activity_json(event_id):
    return jsonify(activities=get_event_activities(event_id))

# API: Outputs CSV of an event activity
@blueprint.route('/event/<int:event_id>/activity.csv')
def event_activity_csv(event_id):
    return Response(stream_with_context(gen_csv(get_event_activities(event_id))),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=activity_list.csv'})

# API: Outputs JSON of recent activity
@blueprint.route('/project/activity.json')
def projects_activity_json():
    activities = [a.data for a in Activity.query.order_by(Activity.id.desc()).limit(30).all()]
    return jsonify(activities=activities)

# API: Outputs JSON of recent activity of a project
@blueprint.route('/project/<int:project_id>/activity.json')
def project_activity_json(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    query = Activity.query.filter_by(project_id=project.id).order_by(Activity.id.desc()).limit(30).all()
    activities = [a.data for a in query]
    return jsonify(project=project.data, activities=activities)

# API: Outputs JSON info for a specific project
@blueprint.route('/project/<int:project_id>/info.json')
def project_info_json(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    project_stars = GetProjectTeam(project)
    activities = []
    for a in project_stars:
        user = {
            'id': a.user.id,
            'name': a.user.username,
            'link': a.user.webpage_url
        }
        activities.append(user)

    data = {
        'project': project.data,
        'phase': project.phase,
        'pitch': project.webembed,
        'is_webembed': project.is_webembed,
        'event': project.event.data,
        'creator': {
            'id': project.user.id,
            'username': project.user.username
        },
        'team': activities
    }

    return jsonify(data)

# ------ SEARCH ---------

# API: Full text search projects
@blueprint.route('/project/search.json')
def project_search_json():
    q = request.args.get('q')
    if q is None or len(q) < 3: return jsonify(projects=[])
    q = "%%%s%%" % q
    projects = Project.query.filter(or_(
        Project.name.like(q),
        Project.summary.like(q),
        Project.longtext.like(q),
        Project.autotext.like(q),
    )).limit(5).all()
    return jsonify(projects=[p.data for p in projects])

# ------ UPDATE ---------

# API: Pushes data into a project
@blueprint.route('/project/push.json', methods=["PUT", "POST"])
def project_push_json():
    data = request.get_json(force=True)
    if not 'key' in data or data['key'] != current_app.config['DRIBDAT_APIKEY']:
        return jsonify(error='Invalid key')
    project = Project.query.filter_by(hashtag=data['hashtag']).first()
    if not project:
        project = Project()
        project.user_id = 1
        project.progress = 0
        project.is_autoupdate = True
        project.event = Event.query.filter_by(is_current=True).first()
    elif project.user_id != 1 or project.is_hidden or not project.is_autoupdate:
        return jsonify(error='Access denied')
    project.hashtag = data['hashtag']
    if 'name' in data and len(data['name']) > 0:
        project.name = data['name']
    else:
        project.name = project.hashtag.replace('-', ' ')
    if 'summary' in data and len(data['summary']) > 0:
        project.summary = data['summary']
    hasLongtext = 'longtext' in data and len(data['longtext']) > 0
    if hasLongtext:
        project.longtext = data['longtext']
    if 'autotext_url' in data and data['autotext_url'].startswith('http'):
        project.autotext_url = data['autotext_url']
        if not project.source_url or project.source_url is '':
            project.source_url = data['autotext_url']
    if 'levelup' in data and 0 < project.progress + data['levelup'] * 10 < 50: # MAX progress
        project.progress = project.progress + data['levelup'] * 10
    # return jsonify(data=data)
    if project.autotext_url is not None and not hasLongtext:
        # Now try to autosync
        data = GetProjectData(project.autotext_url)
        if 'name' in data:
            if len(data['name']) > 0:
                project.name = data['name']
            if 'summary' in data and len(data['summary']) > 0:
                project.summary = data['summary']
            if 'description' in data and len(data['description']) > 0:
                project.longtext = data['description']
            if 'homepage_url' in data and len(data['homepage_url']) > 0:
                project.webpage_url = data['homepage_url']
            if 'source_url' in data and len(data['source_url']) > 0:
                project.source_url = data['source_url']
            if 'image_url' in data and len(data['image_url']) > 0:
                project.image_url = data['image_url']
    project.update()
    db.session.add(project)
    db.session.commit()
    return jsonify(success='Updated', project=project.data)

# ------ FRONTEND -------

# API routine used to sync project data
@blueprint.route('/project/autofill', methods=['GET', 'POST'])
@login_required
def project_autofill():
    url = request.args.get('url')
    data = GetProjectData(url)
    return jsonify(data)
