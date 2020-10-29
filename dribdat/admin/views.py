# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, make_response, request, flash, jsonify
from flask_login import login_required, current_user

from ..extensions import db, cache
from ..decorators import admin_required

from ..user.models import Role, User, Event, Project, Category, Question, Response
from .forms import RoleForm, UserForm, EventForm, ProjectForm, CategoryForm

from datetime import datetime
import random, string

from ..aggregation import (
    GetProjectData, SyncProjectData
)

blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@blueprint.route('/')
@login_required
@admin_required
def index():
    event = Event.query.filter_by(is_current=True).first()
    stats = [
        {
            'value': User.query.count(),
            'text': 'users registered'
        },{
            'value': Event.query.count(),
            'text': 'active events'
        },{
            'value': Project.query.filter(Project.progress<0).count(),
            'text': 'challenges posted'
        },{
            'value': Project.query.filter(Project.progress>=0).count(),
            'text': 'projects started'
        },
    ]
    return render_template('admin/index.html', stats=stats, default_event=event, active='index')


@blueprint.route('/users')
@blueprint.route('/users/pp/<int:page>')
@login_required
@admin_required
def users(page=1):
    users = User.query.order_by(
        User.username.asc()
    ).paginate(page, per_page=20)
    return render_template('admin/users.html', data=users, endpoint='admin.users', active='users')


@blueprint.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = UserForm(obj=user, next=request.args.get('next'))
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by('name')]
    # form.roles.data = [(r.id) for r in user.roles]

    if form.validate_on_submit():
        originalhash = user.password
        del form.id

        user.roles = [Role.query.filter_by(id=r).first() for r in form.roles.data]
        del form.roles

        form.populate_obj(user)
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.password = originalhash
        db.session.add(user)
        db.session.commit()

        flash('User updated.', 'success')
        return users()

    form.roles.data = [(r.id) for r in user.roles]
    return render_template('admin/user.html', user=user, form=form)

@blueprint.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    user = User(active=True)
    form = UserForm(obj=user, next=request.args.get('next'))
    form.roles.choices = [(e.id, e.name) for e in Role.query.order_by('name')]
    form.roles.data = [(r.id) for r in user.roles]

    if form.validate_on_submit():
        del form.id
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        flash('User added.', 'success')
        return users()

    return render_template('admin/usernew.html', form=form)

@blueprint.route('/user/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def user_delete(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    if user.is_admin or user.active:
        flash('Admins and active users may not be deleted.', 'warning')
    elif len(user.projects) > 0:
        pl = ", ".join([str(i.name) for i in user.projects])
        flash('No users owning projects (%s) may be deleted.' % pl, 'warning')
    else:
        user.delete()
        flash('User deleted.', 'success')
    return users()


# Get a reasonably secure password
def get_random_alphanumeric_string(length=24):
    return ''.join((random.SystemRandom().choice(string.ascii_letters + string.digits) for i in range(length)))

@blueprint.route('/user/<int:user_id>/reset/')
@login_required
@admin_required
def reset(user_id):
    """Reset user password."""
    user = User.query.filter_by(id=user_id).first_or_404()
    newpw = get_random_alphanumeric_string()
    user.set_password(newpw)
    db.session.add(user)
    db.session.commit()
    return render_template('admin/reset.html', newpw=newpw, email=user.email)


##############
##############
##############

@blueprint.route('/events')
@login_required
@admin_required
def events():
    events = Event.query.order_by(Event.starts_at.desc()).all()
    return render_template('admin/events.html', events=events, active='events')


@blueprint.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    form = EventForm(obj=event, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(event)
        event.starts_at = datetime.combine(form.starts_date.data, form.starts_time.data)
        event.ends_at = datetime.combine(form.ends_date.data, form.ends_time.data)

        db.session.add(event)
        db.session.commit()

        cache.clear()

        flash('Event updated.', 'success')
        cache.clear()
        return events()

    form.starts_date.data = event.starts_at
    form.starts_time.data = event.starts_at
    form.ends_date.data = event.ends_at
    form.ends_time.data = event.ends_at
    return render_template('admin/event.html', event=event, form=form)

@blueprint.route('/event/new', methods=['GET', 'POST'])
@login_required
@admin_required
def event_new():
    event = Event()
    form = EventForm(obj=event, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(event)
        event.starts_at = datetime.combine(form.starts_date.data, form.starts_time.data)
        event.ends_at = datetime.combine(form.ends_date.data, form.ends_time.data)

        db.session.add(event)
        db.session.commit()

        flash('Event added.', 'success')
        cache.clear()
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
        cache.clear()
        flash('Event deleted.', 'success')
    return events()

@blueprint.route('/event/<int:event_id>/autosync', methods=['GET', 'POST'])
@login_required
@admin_required
def event_autosync(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    count = 0
    for project in event.projects:
        if not project.is_autoupdate: continue
        data = GetProjectData(project.autotext_url)
        if not 'name' in data:
            flash("Could not sync: %s" % project.name, 'warning')
            continue
        SyncProjectData(project, data)
        count += 1
    flash("%d projects synced." % count, 'success')
    return event_projects(event.id)


##############
##############
##############


@blueprint.route('/projects')
@blueprint.route('/projects/pp/<int:page>')
@login_required
@admin_required
def projects(page=1):
    projects = Project.query.order_by(
        Project.updated_at.desc()
    ).paginate(page, per_page=10)
    return render_template('admin/projects.html', data=projects, endpoint='admin.projects', active='projects')


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
    return render_template('admin/projects.html', projects=projects, event=event, active='projects')

@blueprint.route('/event/<int:event_id>/print')
@login_required
@admin_required
def event_print(event_id):
    now = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    projects = projects.filter(Project.progress>=0).order_by(Project.name)
    return render_template('admin/eventprint.html', event=event, projects=projects, curdate=now, active='projects')

@blueprint.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def project_view(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.user_id.choices = [(e.id, "%s" % (e.username)) for e in User.query.filter_by(active=True).order_by('username')]
    form.event_id.choices = [(e.id, e.name) for e in Event.query.order_by(Event.id.desc())]
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    if form.validate_on_submit():
        del form.id
        form.populate_obj(project)
        # Ensure project category remains blank
        if project.category_id == -1: project.category_id = None
        project.update()
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
    cache.clear()
    if project.is_hidden:
        flash('Project is now hidden.', 'success')
    else:
        flash('Project is now visible.', 'success')
    return project_view(project_id)

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
    form.user_id.choices = [(e.id, "%s" % (e.username)) for e in User.query.filter_by(active=True).order_by('username')]
    form.event_id.choices = [(e.id, e.name) for e in Event.query.order_by(Event.id.desc())]
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    if form.validate_on_submit():
        del form.id
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Project added.', 'success')
        return projects()
    return render_template('admin/projectnew.html', form=form)

@blueprint.route('/project/<int:project_id>/autodata')
@login_required
@admin_required
def project_autodata(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    return jsonify(projectdata=GetProjectData(project.autotext_url))


##############
##############
##############

@blueprint.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.event_id.desc()).all()
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
        if category.logo_color == '#000000': category.logo_color = ''

        db.session.add(category)
        db.session.commit()

        cache.clear()
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

        cache.clear()
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
        cache.clear()
        category.delete()
        flash('Category deleted.', 'success')
    return categories()


##############
##############
##############

@blueprint.route('/presets')
@login_required
@admin_required
def presets():
    roles = Role.query.all()
    categories = Category.query.order_by(Category.event_id.desc()).all()
    questions = Question.query.order_by(Question.type, Question.title.asc()).all()
    return render_template('admin/presets.html',
        categories=categories, roles=roles, questions=questions,
        active='roles'
    )

@blueprint.route('/role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def role(role_id):
    role = Role.query.filter_by(id=role_id).first_or_404()
    form = RoleForm(obj=role, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(role)

        db.session.add(role)
        db.session.commit()

        cache.clear()
        flash('Role updated.', 'success')
        return redirect(url_for("admin.presets"))

    return render_template('admin/role.html', role=role, form=form)

@blueprint.route('/role/new', methods=['GET', 'POST'])
@login_required
@admin_required
def role_new():
    role = Role()
    form = RoleForm(obj=role, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(role)

        db.session.add(role)
        db.session.commit()

        cache.clear()
        flash('Role added.', 'success')
        return redirect(url_for("admin.presets"))

    return render_template('admin/rolenew.html', form=form)


@blueprint.route('/role/<int:role_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def role_delete(role_id):
    role = Role.query.filter_by(id=role_id).first_or_404()
    if len(role.users) > 0:
        flash('No users may be assigned to role in order to delete.', 'warning')
    else:
        cache.clear()
        role.delete()
        flash('Role deleted.', 'success')
    return redirect(url_for("admin.presets"))




@blueprint.route('/question/<int:question_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def question(question_id):
  question = Question.query.filter_by(id=question_id).first_or_404()
  form = QuestionForm(obj=question, next=request.args.get('next'))

  if form.validate_on_submit():
      form.populate_obj(question)

      db.session.add(question)
      db.session.commit()

      cache.clear()
      flash('Question updated.', 'success')
      return redirect(url_for("admin.presets"))

  return render_template('admin/question.html', question=question, form=form)

@blueprint.route('/question/new', methods=['GET', 'POST'])
@login_required
@admin_required
def question_new():
  question = Question()
  form = QuestionForm(obj=question, next=request.args.get('next'))

  if form.validate_on_submit():
      form.populate_obj(question)

      db.session.add(question)
      db.session.commit()

      cache.clear()
      flash('Question added.', 'success')
      return redirect(url_for("admin.presets"))

  return render_template('admin/questionnew.html', form=form)


@blueprint.route('/question/<int:question_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def question_delete(question_id):
  question = Question.query.filter_by(id=question_id).first_or_404()
  if len(question.responses) > 0:
      flash('No responses may be assigned to a question in order to delete.', 'warning')
  else:
      cache.clear()
      question.delete()
      flash('Question deleted.', 'success')
  return redirect(url_for("admin.presets"))
