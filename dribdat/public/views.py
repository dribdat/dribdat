# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app, jsonify)
from flask_login import login_required, current_user

from dribdat.user.models import User, Event, Project
from dribdat.public.forms import *
from dribdat.database import db
from dribdat.extensions import cache
from dribdat.aggregation import (
    SyncProjectData, GetProjectData,
    ProjectActivity, IsProjectStarred,
    GetEventUsers
)
from dribdat.user import projectProgressList

from datetime import datetime

blueprint = Blueprint('public', __name__, static_folder="../static")

def current_event(): return Event.query.filter_by(is_current=True).first()


# Renders a static dashboard
@blueprint.route("/dashboard/")
def dashboard():
    return render_template("public/dashboard.html", current_event=current_event())

# Outputs JSON-LD about the current event (see also api.py/info_event_hackathon_json)
@blueprint.route('/hackathon.json')
def info_current_hackathon_json():
    event = Event.query.filter_by(is_current=True).first() or Event.query.order_by(Event.id.desc()).first()
    return jsonify(event.get_schema(request.host_url))

# Renders a simple about page
@blueprint.route("/about/")
def about():
    return render_template("public/about.html", current_event=current_event())

# Favicon just points to a file
@blueprint.route("/favicon.ico")
def favicon():
    return redirect(url_for('static', filename='img/favicon.ico'))

# Home page
@blueprint.route("/")
def home():
    cur_event = current_event()
    if cur_event is not None:
        events = Event.query.filter(Event.id != cur_event.id)
    else:
        events = Event.query
    events = events.order_by(Event.id.desc()).all()
    return render_template("public/home.html",
        events=events, current_event=cur_event)

@blueprint.route('/user/<int:user_id>', methods=['GET'])
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    event = current_event()
    # projects = user.projects
    projects = user.joined_projects()
    return render_template("public/userprofile.html",
        current_event=event, event=event, user=user, projects=projects)

@blueprint.route("/event/<int:event_id>")
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    if request.args.get('embed'):
        return render_template("public/embed.html", current_event=event, projects=projects)
    summaries = [ p.data for p in projects ]
    # Sort projects by reverse score, then name
    summaries.sort(key=lambda x: (
        -x['score'] if isinstance(x['score'], int) else 0,
        x['name'].lower()))
    return render_template("public/event.html",  current_event=event, projects=summaries)

@blueprint.route("/event/<int:event_id>/participants")
def event_participants(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    users = GetEventUsers(event)
    usercount = len(users) if users else 0
    return render_template("public/eventusers.html",
        current_event=event, participants=users, usercount=usercount)

@blueprint.route('/project/<int:project_id>')
def project(project_id):
    return project_action(project_id, None)

@blueprint.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (not current_user.is_anonymous and current_user.is_admin)
    if not allow_edit:
        flash('You do not have access to edit this project.', 'warning')
        return project_action(project_id, None)
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    if form.validate_on_submit():
        del form.id
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Project updated.', 'success')
        project_action(project_id, 'update', False)
        return redirect(url_for('public.project', project_id=project.id))
    return render_template('public/projectedit.html', current_event=event, project=project, form=form)

@blueprint.route('/project/<int:project_id>/post', methods=['GET', 'POST'])
@login_required
def project_post(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (not current_user.is_anonymous and current_user.is_admin)
    if not allow_edit:
        flash('You do not have access to edit this project.', 'warning')
        return project_action(project_id, None)
    form = ProjectPost(obj=project, next=request.args.get('next'))
    form.progress.choices = projectProgressList(event.has_started or event.has_finished)
    if form.validate_on_submit():
        del form.id
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Thanks for your commit!', 'success')
        project_action(project_id, 'update', action='post', text=form.note.data)
        return redirect(url_for('public.project', project_id=project.id))
    return render_template('public/projectpost.html', current_event=event, project=project, form=form)

def project_action(project_id, of_type=None, as_view=True, then_redirect=False, action=None, text=None):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    if of_type is not None:
        ProjectActivity(project, of_type, current_user, action, text)
    if not as_view:
        return True
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (not current_user.is_anonymous and current_user.is_admin)
    allow_edit = allow_edit and not event.lock_editing
    project_stars = project.team()
    latest_activity = project.latest_activity()
    project_signals = project.all_signals()
    if then_redirect:
        return redirect(url_for('public.project', project_id=project.id))
    return render_template('public/project.html', current_event=event, project=project,
        project_starred=starred, project_stars=project_stars, project_signals=project_signals,
        allow_edit=allow_edit, latest_activity=latest_activity)

@blueprint.route('/project/<int:project_id>/star', methods=['GET', 'POST'])
@login_required
def project_star(project_id):
    flash('Welcome to the team!', 'success')
    return project_action(project_id, 'star', then_redirect=True)

@blueprint.route('/project/<int:project_id>/unstar', methods=['GET', 'POST'])
@login_required
def project_unstar(project_id):
    flash('You have left the project', 'success')
    return project_action(project_id, 'unstar', then_redirect=True)

@blueprint.route('/event/<int:event_id>/project/new', methods=['GET', 'POST'])
def project_new(event_id):
    form = None
    event = Event.query.filter_by(id=event_id).first_or_404()
    if event.lock_starting:
        flash('Starting a new project is disabled for this event.', 'error')
        return redirect(url_for('public.event', event_id=event.id))
    if current_user and current_user.is_authenticated:
        project = Project()
        project.user_id = current_user.id
        form = ProjectNew(obj=project, next=request.args.get('next'))
        form.category_id.choices = [(c.id, c.name) for c in project.categories_all(event)]
        form.category_id.choices.insert(0, (-1, ''))
        if form.validate_on_submit():
            del form.id
            form.populate_obj(project)
            project.event = event
            if event.has_started:
                project.progress = 0
            else:
                project.progress = -1 # Start as challenge
            project.update()
            db.session.add(project)
            db.session.commit()
            flash('New challenge added.', 'success')
            project_action(project.id, 'create', False)
            cache.clear()
            project_action(project.id, 'star', False)
            if len(project.autotext_url)>1:
                return project_autoupdate(project.id)
            else:
                return redirect(url_for('public.project', project_id=project.id))
    return render_template('public/projectnew.html', current_event=event, form=form)

@blueprint.route('/project/<int:project_id>/autoupdate')
@login_required
def project_autoupdate(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (not current_user.is_anonymous and current_user.is_admin)
    if not allow_edit or project.is_hidden or not project.is_autoupdate:
        flash('You may not sync this project.', 'warning')
        return project_action(project_id)
    data = GetProjectData(project.autotext_url)
    if not 'name' in data:
        flash("Could not sync: check the Remote Link.", 'warning')
        return project_action(project_id)
    SyncProjectData(project, data)
    project_action(project.id, 'update', action='sync', text=str(len(project.autotext)) + ' bytes')
    flash("Project data synced from %s" % data['type'], 'success')
    return redirect(url_for('public.project', project_id=project.id))
