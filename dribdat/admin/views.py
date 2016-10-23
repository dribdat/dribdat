# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, make_response, request, flash, jsonify
from flask_login import login_required, current_user

from ..extensions import db
from ..decorators import admin_required

from ..user.models import User, Event, Project, Category
from .forms import UserForm, EventForm, ProjectForm, CategoryForm

from flask import Response, stream_with_context
import io, csv

import json
import datetime

blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@blueprint.route('/')
@login_required
@admin_required
def index():
    users = User.query.all()
    return render_template('admin/index.html', users=users, active='index')


@blueprint.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users, active='users')


@blueprint.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
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

        flash('User updated.', 'success')
        return users()

    return render_template('admin/user.html', user=user, form=form)

@blueprint.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    user = User()
    form = UserForm(obj=user, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        flash('User added.', 'success')
        return users()

    return render_template('admin/usernew.html', form=form)

##############
##############
##############

@blueprint.route('/events')
@login_required
@admin_required
def events():
    events = Event.query.all()
    return render_template('admin/events.html', events=events, active='events')


@blueprint.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    form = EventForm(obj=event, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(event)

        db.session.add(event)
        db.session.commit()

        flash('Event updated.', 'success')
        return events()

    return render_template('admin/event.html', event=event, form=form)

@blueprint.route('/event/new', methods=['GET', 'POST'])
@login_required
@admin_required
def event_new():
    event = Event()
    form = EventForm(obj=event, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(event)

        db.session.add(event)
        db.session.commit()

        flash('Event added.', 'success')
        return events()

    return render_template('admin/eventnew.html', form=form)

@blueprint.route('/event/<int:event_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def event_delete(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    if event.is_current:
        flash('Event must not be set as current in order to delete.', 'warning')
    elif len(event.categories) > 0:
        flash('No categories may be assigned to event in order to delete.', 'warning')
    elif len(event.projects) > 0:
        flash('No projects may be assigned to event in order to delete.', 'warning')
    else:
        event.delete()
        flash('Event deleted.', 'success')
    return events()

##############
##############
##############


@blueprint.route('/projects')
@login_required
@admin_required
def projects():
    # TODO: pagination...
    projects = Project.query.order_by(Project.id.desc()).all()
    return render_template('admin/projects.html', projects=projects, active='projects')

@blueprint.route('/category/<int:category_id>/projects')
@login_required
@admin_required
def category_projects(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    projects = Project.query.filter_by(category_id=category_id).order_by(Project.id.desc())
    return render_template('admin/projects.html', projects=projects, category_name=category.name, active='projects')

@blueprint.route('/event/<int:event_id>/projects')
@login_required
@admin_required
def event_projects(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id).order_by(Project.id.desc())
    return render_template('admin/projects.html', projects=projects, event_name=event.name, active='projects')

@blueprint.route('/event/<int:event_id>/print')
@login_required
@admin_required
def event_print(event_id):
    now = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False).order_by(Project.name)
    return render_template('admin/eventprint.html', event=event, projects=projects, curdate=now, active='projects')

# Collect all projects for current event
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

# Outputs JSON of all projects
@blueprint.route('/event/<int:event_id>/projects.json')
def project_list_json(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(projects=project_list(event_id), event=event.data)

# Outputs CSV of all projects
@blueprint.route('/event/<int:event_id>/projects.csv')
def project_list_csv(event_id):
    return Response(stream_with_context(gen_csv(project_list(event_id))),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=project_list.csv'})

@blueprint.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def project(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.user_id.choices = [(e.id, "%s" % (e.username)) for e in User.query.order_by('username')]
    form.event_id.choices = [(e.id, e.name) for e in Event.query.order_by('name')]
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]

    if form.validate_on_submit():
        form.populate_obj(project)

        db.session.add(project)
        db.session.commit()

        flash('Project updated.', 'success')
        return projects()

    return render_template('admin/project.html', project=project, form=form)

@blueprint.route('/project/<int:project_id>/toggle', methods=['GET', 'POST'])
@login_required
@admin_required
def project_toggle(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    project.is_hidden = not project.is_hidden
    project.save()
    if project.is_hidden:
        flash('Project is now hidden.', 'success')
    else:
        flash('Project is now visible.', 'success')
    return projects()

@blueprint.route('/project/<int:project_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def project_delete(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    if not project.is_hidden:
        flash('Project must be disabled.', 'warning')
    else:
        for a in project.activities: a.delete()
        project.delete()
        flash('Project deleted.', 'success')
    return projects()

@blueprint.route('/project/new', methods=['GET', 'POST'])
@login_required
@admin_required
def project_new():
    project = Project()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.user_id.choices = [(e.id, "%s" % (e.username)) for e in User.query.order_by('username')]
    form.event_id.choices = [(e.id, e.name) for e in Event.query.order_by('name')]
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]

    if form.validate_on_submit():
        form.populate_obj(project)

        db.session.add(project)
        db.session.commit()

        flash('Project added.', 'success')
        return projects()

    return render_template('admin/projectnew.html', form=form)

##############
##############
##############

@blueprint.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.id.desc()).all()
    return render_template('admin/categories.html', categories=categories, active='categories')


@blueprint.route('/category/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    form = CategoryForm(obj=category, next=request.args.get('next'))
    form.event_id.choices = [(e.id, e.name) for e in Event.query.order_by('name')]
    form.event_id.choices.insert(0, (-1, ''))

    if form.validate_on_submit():
        form.populate_obj(category)
        if category.event_id == -1: category.event_id = None

        db.session.add(category)
        db.session.commit()

        flash('Category updated.', 'success')
        return categories()

    return render_template('admin/category.html', category=category, form=form)

@blueprint.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def category_new():
    category = Category()
    form = CategoryForm(obj=category, next=request.args.get('next'))
    form.event_id.choices = [(e.id, e.name) for e in Event.query.order_by('name')]
    form.event_id.choices.insert(0, (-1, ''))

    if form.validate_on_submit():
        form.populate_obj(category)
        if category.event_id == -1: category.event_id = None

        db.session.add(category)
        db.session.commit()

        flash('Category added.', 'success')
        return categories()

    return render_template('admin/categorynew.html', form=form)


@blueprint.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def category_delete(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    if len(category.projects) > 0:
        flash('No projects may be assigned to category in order to delete.', 'warning')
    else:
        category.delete()
        flash('Category deleted.', 'success')
    return categories()
