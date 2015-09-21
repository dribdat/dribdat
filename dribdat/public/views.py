# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app)
from flask_login import login_user, login_required, logout_user

from dribdat.extensions import login_manager
from dribdat.user.models import User, Event, Project
from dribdat.public.forms import LoginForm
from dribdat.user.forms import RegisterForm
from dribdat.admin.forms import ProjectForm
from dribdat.utils import flash_errors
from dribdat.database import db

blueprint = Blueprint('public', __name__, static_folder="../static")

@login_manager.user_loader
def load_user(id):
    return User.get_by_id(int(id))

@blueprint.route("/", methods=["GET", "POST"])
def home():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", 'success')
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    event = Event.query.first()
    return render_template("public/home.html", form=form, current_event=event)

@blueprint.route("/about/")
def about():
    form = LoginForm(request.form)
    return render_template("public/about.html", current_event, form=form)

@blueprint.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        new_user = User.create(
                        username=form.username.data,
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        email=form.email.data,
                        password=form.password.data,
                        active=True)
        flash("Thank you for registering. You can now log in.", 'success')
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    event = Event.query.first()
    return render_template('public/register.html', current_event=event, form=form)

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
    event = Event.query.filter_by(id=project.event_id).first_or_404()
    return render_template('public/project.html', current_event=event, project=project)

@blueprint.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    event = Event.query.first()
    form.event_id.choices = [(event.id, event.name)]
    if form.validate_on_submit():
        form.populate_obj(project)
        db.session.add(project)
        db.session.commit()
        flash('Project updated.', 'success')
        return render_template('public/project.html', current_event=event, project=project)
    return render_template('public/projectedit.html', current_event=event, project=project, form=form)

@blueprint.route('/project/new', methods=['GET', 'POST'])
@login_required
def project_new():
    project = Project()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    event = Event.query.first()
    form.event_id.choices = [(event.id, event.name)]
    if form.validate_on_submit():
        form.populate_obj(project)
        db.session.add(project)
        db.session.commit()
        flash('Project added.', 'success')
        return render_template('public/project.html', current_event=event, project=project)
    return render_template('public/projectnew.html', current_event=event, form=form)
