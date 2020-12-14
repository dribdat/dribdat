# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app, jsonify)
from flask_login import login_required, current_user

from dribdat.user.models import User, Event, Project, Resource
from dribdat.public.forms import (
    LoginForm, UserForm,
    ProjectNew, ProjectForm,
    ProjectPost, ResourceForm,
)
from dribdat.database import db
from dribdat.extensions import cache
from dribdat.aggregation import (
    SyncProjectData, GetProjectData,
    ProjectActivity, IsProjectStarred,
    GetEventUsers, SuggestionsByProgress,
)
from dribdat.user import projectProgressList

from datetime import datetime

blueprint = Blueprint('public', __name__, static_folder="../static")

def current_event(): return Event.query.filter_by(is_current=True).first()


# Renders a static dashboard
@blueprint.route("/dashboard/")
def dashboard():
    event = current_event()
    if not event: return 'No current event'
    wall = 'twitter.com' in event.community_url
    return render_template("public/dashboard.html", current_event=event, with_social_wall=wall)

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
    events = events.filter(Event.is_hidden != True)
    events = events.order_by(Event.id.desc()).all()
    return render_template("public/home.html",
        events=events, current_event=cur_event)

@blueprint.route('/user/<username>', methods=['GET'])
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not user.active:
        return "User deactivated. Please contact an event organizer."
    event = current_event()
    cert_path = user.get_cert_path(event)
    # projects = user.projects
    projects = user.joined_projects()
    posts = user.latest_posts()
    submissions = Resource.query.filter_by(user_id=user.id).order_by(Resource.id.desc()).all()
    return render_template("public/userprofile.html",
        current_event=event, event=event, user=user, cert_path=cert_path,
        projects=projects, submissions=submissions, posts=posts)

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
    project_count = projects.count()
    return render_template("public/event.html", current_event=event,
        projects=summaries, project_count=project_count)

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
    # Populate progress dialog
    form.progress.choices = projectProgressList(event.has_started or event.has_finished)
    # Populate resource list
    resources = Resource.query.filter_by(is_visible=True).order_by(Resource.type_id).all()
    resource_list = [(0, '')]
    resource_list.extend([(r.id, r.of_type + ': ' + r.name) for r in resources])
    form.resource.choices = resource_list
    # Process form
    if form.validate_on_submit():
        del form.id
        if form.resource.data == 0:
            form.resource.data = None
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Thanks for your commit!', 'success')
        project_action(project_id, 'update', action='post', text=form.note.data, resource=form.resource.data)
        return redirect(url_for('public.project', project_id=project.id))
    return render_template('public/projectpost.html', current_event=event, project=project, form=form)

def project_action(project_id, of_type=None, as_view=True, then_redirect=False, action=None, text=None, resource=None):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    if of_type is not None:
        ProjectActivity(project, of_type, current_user, action, text, resource)
    if not as_view:
        return True
    if then_redirect:
        return redirect(url_for('public.project', project_id=project.id))
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (not current_user.is_anonymous and current_user.is_admin)
    allow_edit = allow_edit and not event.lock_editing
    project_team = project.team()
    latest_activity = project.latest_activity()
    project_signals = project.all_signals()
    suggestions = SuggestionsByProgress(project.progress)
    return render_template('public/project.html', current_event=event, project=project,
        project_starred=starred, project_team=project_team, project_signals=project_signals, suggestions=suggestions,
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


@blueprint.route('/resource/<int:resource_id>', methods=['GET'])
def resource(resource_id):
    resource = Resource.query.filter_by(id=resource_id).first_or_404()
    projects = [ c.project for c in resource.get_comments() ]
    return render_template('public/resource.html', resource=resource, projects=projects)

@blueprint.route('/resource/post', methods=['GET', 'POST'])
@login_required
def resource_post():
    resource = Resource()
    form = ResourceForm(obj=resource)
    if form.validate_on_submit():
        form.populate_obj(resource)
        resource.user_id = current_user.id
        resource.is_visible = current_app.config['DRIBDAT_SHOW_SUBMITS']
        db.session.add(resource)
        db.session.commit()
        flash('Thanks for the tip! Your suggestions are visible in your profile.', 'success')
        return redirect(url_for('public.user', username=current_user.username))
    return render_template('public/resourcenew.html', form=form)

@blueprint.route('/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def resource_edit(resource_id):
    resource = Resource.query.filter_by(id=resource_id).first_or_404()
    event = current_event()
    allow_edit = not current_user.is_anonymous and current_user == resource.user or current_user.is_admin
    if not allow_edit:
        flash('You do not have access to edit this resource.', 'warning')
        return redirect(url_for('public.home'))
    form = ResourceForm(obj=resource)
    if form.validate_on_submit():
        form.populate_obj(resource)
        db.session.add(resource)
        db.session.commit()
        flash('Changes saved.', 'success')
        return redirect(url_for('public.user', username=current_user.username))
    return render_template('public/resourceedit.html', resource=resource, form=form)
