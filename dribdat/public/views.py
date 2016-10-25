# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app, jsonify)
from flask_login import login_user, login_required, logout_user, current_user

from dribdat.extensions import login_manager
from dribdat.user.models import User, Event, Project
from dribdat.public.forms import LoginForm, UserForm, ProjectForm
from dribdat.user.forms import RegisterForm
from dribdat.utils import flash_errors
from dribdat.database import db
from dribdat.aggregation import GetProjectData, ProjectActivity, IsProjectStarred, GetProjectTeam

from datetime import datetime

blueprint = Blueprint('public', __name__, static_folder="../static")

def get_current_event():
    event = Event.query.filter_by(is_current=True).first()
    return event

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

@blueprint.route("/")
def home():
    event = get_current_event()
    if event is not None:
        events = Event.query.filter(Event.id != event.id)
    else:
        events = Event.query.all()
    return render_template("public/home.html", events=events, current_event=event)

@blueprint.route("/about/")
def about():
    return render_template("public/about.html", current_event=get_current_event())

@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user, remember=True)
            flash("You are logged in.", 'success')
            redirect_url = request.args.get("next") or url_for("public.home")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/login.html", current_event=get_current_event(), form=form)

@blueprint.route('/logout/')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    """Register new user."""
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.args.get('name'):
        form.username.data = request.args.get('name')
    if request.args.get('email'):
        form.email.data = request.args.get('email')
    if request.args.get('web'):
        form.webpage_url.data = request.args.get('web')
    if form.validate_on_submit():
        new_user = User.create(
                        username=form.username.data,
                        email=form.email.data,
                        webpage_url=form.webpage_url.data,
                        password=form.password.data,
                        active=True)
        new_user.socialize()
        if User.query.count() == 1:
            new_user.is_admin = True
            new_user.save()
            flash("Administrative user created - have fun with DRIBDAT!", 'success')
        else:
            flash("Thank you for registering. You can now log in and submit projects.", 'success')
        return redirect(url_for('public.login'))
    else:
        flash_errors(form)
    return render_template('public/register.html', current_event=get_current_event(), form=form)

@blueprint.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    user = current_user
    form = UserForm(obj=user, next=request.args.get('next'))
    if form.validate_on_submit():
        originalhash = user.password
        form.populate_obj(user)
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.password = originalhash
        db.session.add(user)
        db.session.commit()
        user.socialize()
        flash('Profile updated.', 'success')
    return render_template('public/user.html', user=user, form=form)

@blueprint.route("/event/<int:event_id>")
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    return render_template("public/event.html",  current_event=event, projects=projects)

@blueprint.route('/project/<int:project_id>')
def project(project_id):
    return project_action(project_id, None)

@blueprint.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    if project.user_id != current_user.id:
        flash('You do not have access to edit this project.', 'warning')
        return project_action(project_id, None)
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    if form.validate_on_submit():
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        flash('Project updated.', 'success')
        return project_action(project_id, 'update')
    return render_template('public/projectedit.html', current_event=event, project=project, form=form)

def project_action(project_id, of_type):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    if of_type is not None:
        ProjectActivity(project, of_type, current_user)
    project_starred = current_user and current_user.is_authenticated and IsProjectStarred(project, current_user)
    project_stars = GetProjectTeam(project)
    return render_template('public/project.html', current_event=event, project=project,
        project_starred=project_starred, project_stars=project_stars)

@blueprint.route('/project/<int:project_id>/star', methods=['GET', 'POST'])
@login_required
def project_star(project_id):
    flash('Thanks for your support!', 'success')
    return project_action(project_id, 'star')

@blueprint.route('/project/<int:project_id>/unstar', methods=['GET', 'POST'])
@login_required
def project_unstar(project_id):
    flash('Project un-starred', 'success')
    return project_action(project_id, 'unstar')

@blueprint.route('/project/new', methods=['GET', 'POST'])
@login_required
def project_new():
    project = Project()
    project.user_id = current_user.id
    form = ProjectForm(obj=project, next=request.args.get('next'))
    event = get_current_event()
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    if form.validate_on_submit():
        form.populate_obj(project)
        project.event = event
        project.update()
        db.session.add(project)
        db.session.commit()
        flash('Project added.', 'success')
        return project_action(project.id, 'create')
    del form.logo_icon
    del form.logo_color
    return render_template('public/projectnew.html', current_event=event, form=form)

# API routine used to sync project data
@blueprint.route('/project/autofill', methods=['GET', 'POST'])
@login_required
def project_autofill():
    url = request.args.get('url')
    data = GetProjectData(url)
    return jsonify(data)

@blueprint.route('/project/<int:project_id>/autoupdate')
@login_required
def project_autoupdate(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    if project.user_id != current_user.id or project.is_hidden or not project.is_autoupdate:
        flash('You cannot sync this project.', 'warning')
        return project_action(project_id, None)
    data = GetProjectData(project.autotext_url)
    if not 'name' in data:
        flash("Project could not be synced: check the autoupdate link.", 'warning')
        return project_action(project_id, None)
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
    flash("Project data synced.", 'success')
    return project_action(project_id, 'update')
