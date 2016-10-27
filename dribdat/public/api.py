# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, make_response, request, flash, jsonify
from flask_login import login_required, current_user

from ..extensions import db
from ..utils import timesince

from ..user.models import Event, Project, Category, Activity

from flask import Response, stream_with_context
import io, csv, json

blueprint = Blueprint('api', __name__, url_prefix='/api')


# Collect all projects for an event
def project_list(event_id):
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    summaries = [ p.data for p in projects ]
    summaries.sort(key=lambda x: x['score'], reverse=True)
    return summaries

# Generate a CSV file
def gen_csv(csvdata):
    output = io.BytesIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(csvdata[0].keys())
    for rk in csvdata:
        writer.writerow(rk.values())
    return output.getvalue()


# API: Outputs JSON about an event
@blueprint.route('/event/<int:event_id>/info.json')
def info_event_json(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(event=event.data, timeuntil=timesince(event.countdown, until=True))

# API: Outputs JSON about the current event
@blueprint.route('/event/current/info.json')
def info_current_event_json():
    event = Event.query.filter_by(is_current=True).first()
    return info_event_json(event.id)

# API: Outputs JSON of all projects in an event
@blueprint.route('/event/<int:event_id>/projects.json')
def project_list_json(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(projects=project_list(event_id), event=event.data)

# API: Outputs JSON of projects in the current event
@blueprint.route('/event/current/projects.json')
def project_list_current_json():
    event = Event.query.filter_by(is_current=True).first()
    return project_list_json(event.id)

# API: Outputs CSV of all projects in an event
@blueprint.route('/event/<int:event_id>/projects.csv')
def project_list_csv(event_id):
    return Response(stream_with_context(gen_csv(project_list(event_id))),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=project_list.csv'})

# API: Outputs JSON of all recent activity
@blueprint.route('/projects/activity.json')
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
