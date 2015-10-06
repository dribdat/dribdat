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
from dribdat.aggregation import GetProjectData, ProjectActivity

blueprint = Blueprint('public', __name__, static_folder="../static")

def get_current_event():
    return Event.query.filter_by(is_current=True).first()

@login_manager.user_loader
def load_user(id):
    return User.get_by_id(int(id))

@blueprint.route("/")
def home():
    return render_template("public/home.html", current_event=get_current_event())

@blueprint.route("/about/")
def about():
    return render_template("public/about.html", current_event=get_current_event())

@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", 'success')
            redirect_url = request.args.get("next") or url_for("public.home")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/login.html", current_event=get_current_event(), form=form)

@blueprint.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.args.get('name'):
        form.username.data = request.args.get('name')
    if request.args.get('email'):
        form.email.data = request.args.get('email')
    if request.args.get('team'):
        form.teamname.data = request.args.get('team')
    if request.args.get('web'):
        form.webpage_url.data = request.args.get('web')
    if form.validate_on_submit():
        new_user = User.create(
                        username=form.username.data,
                        email=form.email.data,
                        teamname=form.teamname.data,
                        webpage_url=form.webpage_url.data,
                        password=form.password.data,
                        active=True)
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

        flash('Profile updated.', 'success')
    return render_template('public/user.html', user=user, form=form)

@blueprint.route("/events")
def events():
    q = Event.query
    event = q.first()
    events = q.all()
    return render_template("public/events.html", current_event=event, events=events)

@blueprint.route("/event/<int:event_id>")
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id)
    return render_template("public/event.html",  current_event=event, projects=projects)

@blueprint.route('/project/<int:project_id>')
def project(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    return render_template('public/project.html', current_event=event, project=project)

@blueprint.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    if project.user_id != current_user.id:
        flash('You do not have access to edit this project.', 'warning')
        return render_template('public/project.html', current_event=event, project=project)
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    if form.validate_on_submit():
        form.populate_obj(project)
        if project.category_id == -1: project.category_id = None
        db.session.add(project)
        db.session.commit()
        flash('Project updated.', 'success')
        ProjectActivity(project, 'update', current_user)
        return render_template('public/project.html', current_event=event, project=project)
    return render_template('public/projectedit.html', current_event=event, project=project, form=form)

@blueprint.route('/project/<int:project_id>/star', methods=['GET', 'POST'])
@login_required
def project_star(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    ProjectActivity(project, 'star', current_user)
    flash('Thanks for your support!', 'success')
    return render_template('public/project.html', current_event=event, project=project)

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
        if project.category_id == -1: project.category_id = None
        db.session.add(project)
        db.session.commit()
        flash('Project added.', 'success')
        ProjectActivity(project, 'create', current_user)
        return render_template('public/project.html', current_event=event, project=project)
    return render_template('public/projectnew.html', current_event=event, form=form)

@blueprint.route('/project/autofill', methods=['GET', 'POST'])
@login_required
def project_autofill():
    url = request.args.get('url')
    data = GetProjectData(url)
    return jsonify(data)
