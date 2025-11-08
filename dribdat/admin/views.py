# -*- coding: utf-8 -*-

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify
)
from flask_login import login_required

from ..utils import (
    unpack_csvlist, pack_csvlist,
    sanitize_input, get_time_note,
    get_random_alphanumeric_string
)
from ..extensions import db, cache
from ..decorators import admin_required
from ..api.parser import GetProjectData
from ..aggregation import SyncProjectData
from ..user.models import Role, User, Event, Activity, Project, Category
from ..user import getProjectStages
from ..public.userhelper import get_user_by_name
from .forms import (
    RoleForm, CategoryForm,
    EventForm, ProjectForm,
    UserForm, UserProfileForm,
)

from datetime import datetime
from dribdat.futures import UTC
from random import randrange


blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@blueprint.route('/')
@login_required
@admin_required
def index():
    current_event = Event.query.filter_by(is_current=True).first()
    if current_event is None:
        sum_hidden = 0
    else:
        sum_hidden = Project.query.filter(Project.event_id==current_event.id) \
                                  .filter(Project.is_hidden).count()
    stats = [
        {
            'value': Event.query.count(),
            'text': 'Events',
            'icon': 'calendar',
            'height': 6
        }, {
            'value': User.query.count(),
            'text': 'Users',
            'icon': 'user',
            'height': 7
        }, {
            'value': Project.query.filter(Project.progress == 0).count(),
            'text': 'Projects',
            'icon': 'trophy',
            'height': 8
        }, {
            'value': Project.query.filter(Project.progress > 0).count(),
            'text': 'Teams',
            'icon': 'star',
            'height': 9
        }, {
            'value': Activity.query.count(),
            'text': 'Dribs',
            'icon': 'comments',
            'height': 10
        },
    ]

    ADMIN_WISDOM = [
        "Welcome, Admin! Today's hack-weather is pleasantly warm with patches of cybershine.",
        "A hacker's work is never done, but their motherboard is always on the fritz.",
        "In a world of 1s and 0s, the only constant is rebooting your expectations.",
        "The cloud is just someone else's computer, and it's always raining malware.",
        "Code is like a joke: if you have to explain it, it's not working properly.",
        "The only thing more abundant than bugs in the system is the number of users who think they're features.",
    ]
    motd = ADMIN_WISDOM.pop(randrange(len(ADMIN_WISDOM)))

    msgs = []
    if sum_hidden > 0:
        msgs.append('%d hidden projects in the featured event ' % sum_hidden + \
              ' may need moderation.')

    return render_template('admin/index.html',
                           stats=stats, motd=motd, msgs=' '.join(msgs),
                           timeinfo=get_time_note(),
                           event=current_event, active='index')


@blueprint.route('/users')
@blueprint.route('/users/pp/<int:page>')
@login_required
@admin_required
def users(page=1):
    sort_by = request.args.get('sort')
    if sort_by == 'id':
        users = User.query.order_by(
            User.id.asc()
        )
    elif sort_by == 'admin':
        users = User.query.order_by(
            User.is_admin.desc()
        )
    elif sort_by == 'sso':
        users = User.query.order_by(
            User.sso_id.desc()
        )
    elif sort_by == 'updated':
        users = User.query.order_by(
            User.updated_at.desc()
        )
    elif sort_by == 'email':
        users = User.query.order_by(
            User.email.asc()
        )
    elif sort_by == 'username':
        users = User.query.order_by(
            User.username.asc()
        )
    else:  # Default: created
        sort_by = 'created'
        users = User.query.order_by(
            User.created_at.desc()
        )
    search_by = request.args.get('search')
    if search_by and len(search_by) > 1:
        q = "%%%s%%" % search_by.lower()
        if '@' in search_by:
            users = users.filter(User.email.ilike(q))
        else:
            users = users.filter(User.username.ilike(q))
    userpages = users.paginate(page=page, per_page=20)
    return render_template('admin/users.html', sort_by=sort_by,
                           data=userpages, endpoint='admin.users', active='users')


@blueprint.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = UserForm(obj=user, next=request.args.get('next'))
    if form.is_submitted() and form.validate():
        originalhash = user.password
        user.username = sanitize_input(form.username.data)

        # Check unique email (why does this sometimes pass validation?)
        if form.email.data != user.email:
            if User.query.filter_by(email=form.email.data).count() > 0:
                flash('A user with this e-mail already exists.', 'warning')
                return render_template('admin/useredit.html', user=user, form=form)

        del form.id
        del form.username
        form.populate_obj(user)

        # Update password if changed
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.password = originalhash

        user.updated_at = datetime.now(UTC)
        db.session.add(user)
        db.session.commit()
        user.socialize()

        flash('User updated.', 'success')
        return redirect(url_for("admin.users"))

    return render_template('admin/useredit.html', user=user, form=form)


@blueprint.route('/user/<int:user_id>/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def user_profile(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = UserProfileForm(obj=user, next=request.args.get('next'))
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by('name')]
    if form.is_submitted() and form.validate():
        del form.id
        # Assign roles
        user.roles = [Role.query.filter_by(
            id=r).first() for r in form.roles.data]
        del form.roles

        # Assign CSV data
        user.my_wishes = unpack_csvlist(form.my_wishes.data)
        user.my_skills = unpack_csvlist(form.my_skills.data)
        del form.my_wishes # avoid setting it again
        del form.my_skills # avoid setting it again

        form.populate_obj(user)
        user.updated_at = datetime.now(UTC)
        db.session.add(user)
        db.session.commit()
        user.socialize()

        flash('User updated.', 'success')
        return redirect(url_for("admin.user", user_id=user_id))

    if 'my_skills' in dir(form):
        form.my_skills.data = pack_csvlist(user.my_skills, ", ")
        form.my_wishes.data = pack_csvlist(user.my_wishes, ", ")
    if not form.roles.choices:
        del form.roles
    else:
        form.roles.data = [(r.id) for r in user.roles]
    return render_template('admin/userprofile.html', user=user, form=form)


@blueprint.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    user = User()
    user.active = True
    form = UserForm(obj=user, next=request.args.get('next'))
    del form.active
    if form.is_submitted() and form.validate():
        del form.id
        user.username = sanitize_input(form.username.data)
        if User.query.filter_by(email=form.email.data).first():
            flash('E-mail must be unique.', 'danger')
        else:
            del form.username
            form.populate_obj(user)
            if form.password.data:
                user.set_password(form.password.data)
            else:
                user.set_password(get_random_alphanumeric_string())
            db.session.add(user)
            db.session.commit()

            flash('User added.', 'success')
            return redirect(url_for("admin.users"))

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
    return redirect(url_for("admin.users"))


@blueprint.route('/user/<int:user_id>/reset/')
@login_required
@admin_required
def user_reset(user_id):
    """Reset user password."""
    user = User.query.filter_by(id=user_id).first_or_404()
    newpw = get_random_alphanumeric_string()
    user.set_password(newpw)
    db.session.add(user)
    db.session.commit()
    return render_template('admin/reset.html', newpw=newpw, email=user.email)


@blueprint.route('/user/<int:user_id>/deactivate/')
@login_required
@admin_required
def user_deactivate(user_id, reactivate=False):
    """Manage activation of user account."""
    user = User.query.filter_by(id=user_id).first_or_404()
    user.active = reactivate
    db.session.add(user)
    db.session.commit()
    if reactivate:
        flash('User %s is now active.' % user.username, 'success')
    else:
        flash('User %s deactivated.' % user.username, 'warning')
    return redirect(url_for("admin.users"))


@blueprint.route('/user/<int:user_id>/reactivate/')
@login_required
@admin_required
def user_reactivate(user_id):
    """Reactivate user account."""
    return user_deactivate(user_id, True)


@blueprint.route('/user/<int:user_id>/clearsso/')
@login_required
@admin_required
def user_clearsso(user_id):
    """Clear SSO from a user account."""
    user = User.query.filter_by(id=user_id).first_or_404()
    user.sso_id = None
    db.session.add(user)
    db.session.commit()
    flash('SSO for %s deactivated.' % user.username, 'warning')
    return redirect(url_for("admin.users"))

##############
##############
##############


@blueprint.route('/events')
@login_required
@admin_required
def events():
    page = int(request.args.get('page', 1))
    events = Event.query.order_by(Event.starts_at.desc())
    eventpages = events.paginate(page=page, per_page=10)
    return render_template('admin/events.html',
        data=eventpages, endpoint='admin.events',
        active='events')


@blueprint.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()

    if event.location_lat is None or event.location_lon is None:
        event.location_lat = event.location_lon = 0

    form = EventForm(obj=event, next=request.args.get('next'))

    if form.is_submitted() and form.validate():
        form.populate_obj(event)
        event.starts_at = datetime.combine(
            form.starts_date.data, form.starts_time.data)
        event.ends_at = datetime.combine(
            form.ends_date.data, form.ends_time.data)
        event.user = get_user_by_name(form.user_name.data)

        db.session.add(event)
        db.session.commit()

        cache.clear()

        flash('Event updated.', 'success')
        return redirect(url_for("admin.events"))

    form.starts_date.data = event.starts_at
    form.starts_time.data = event.starts_at
    form.ends_date.data = event.ends_at
    form.ends_time.data = event.ends_at
    if event.user:
        form.user_name.data = event.user.username
    return render_template('admin/event.html', event=event, form=form)


@blueprint.route('/event/<int:event_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def event_delete(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    if event.is_current:
        flash('Event must not be set as current to delete.', 'warning')
    elif len(event.categories) > 0:
        flash('No categories may be assigned to event to delete.', 'warning')
    elif len(event.projects) > 0:
        flash('No projects may be assigned to event to delete.', 'warning')
    else:
        event.delete()
        cache.clear()
        flash('Event deleted.', 'success')
    return events()


@blueprint.route('/event/<int:event_id>/copy', methods=['GET', 'POST'])
@login_required
@admin_required
def event_copy(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    new_event = Event(name='Copy')
    new_event.set_from_data(event.data)
    new_event.name = new_event.name + ' (copy)'
    new_event.save()
    return redirect(url_for("admin.event", event_id=new_event.id))


@blueprint.route('/event/<int:event_id>/feature', methods=['GET', 'POST'])
@login_required
@admin_required
def event_feature(event_id):
    for event in Event.query.filter_by(is_current=True).all():
        event.is_current = False
        event.save()
    event = Event.query.filter_by(id=event_id).first_or_404()
    event.is_current = True
    event.save()
    return redirect(url_for("admin.events"))


@blueprint.route('/resource/area', methods=['GET', 'POST'])
@login_required
@admin_required
def event_resource_area():
    event = Event.query.filter_by(lock_resources=True).first()
    if event:
        return redirect(url_for("admin.event_projects", event_id=event.id))
    new_event = Event(name='Resources')
    new_event.lock_resources = True
    new_event.save()
    return redirect(url_for("admin.event_projects", event_id=new_event.id))


@blueprint.route('/event/<int:event_id>/autosync', methods=['GET', 'POST'])
@login_required
@admin_required
def event_autosync(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    count = 0
    for project in event.projects:
        if not project.is_syncable:
            continue
        data = GetProjectData(project.autotext_url, True)
        if 'name' not in data:
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
    )
    search_by = request.args.get('search')
    if search_by and len(search_by) > 1:
        q = "%%%s%%" % search_by.lower()
        projects = projects.filter(Project.name.ilike(q))
    projectpages = projects.paginate(page=page, per_page=10)
    return render_template('admin/projects.html',
                           data=projectpages, endpoint='admin.projects',
                           active='projects')


@blueprint.route('/category/<int:category_id>/projects')
@login_required
@admin_required
def category_projects(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    projects = Project.query.filter_by(
        category_id=category_id).order_by(Project.id.desc())
    return render_template('admin/projects.html', projects=projects,
                           category_name=category.name, active='projects')


@blueprint.route('/event/<int:event_id>/projects')
@login_required
@admin_required
def event_projects(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(
        event_id=event_id).order_by(Project.id.desc())
    return render_template('admin/projects.html',
                           projects=projects, event=event, active='projects')


@blueprint.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def project_view(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    #form.event_id.choices = [(e.id, e.name)
    #                         for e in Event.query.order_by(Event.id.desc())]
    form.category_id.choices = [(c.id, c.name)
                                for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))
    # Check event in range
    if form.event_id.data not in [e.id for e in Event.query.all()]:
        flash('You must set the Event ID to a valid number', 'danger')

    # Standard validation
    elif form.is_submitted() and form.validate():
        del form.id
        form.populate_obj(project)
        # Ensure project category remains blank
        if project.category_id == -1:
            project.category_id = None
        # Assign technai from CSV
        project.technai = unpack_csvlist(form.technai.data)
        del form.technai # avoid setting it again
        # Assign owner if selected
        project.user = get_user_by_name(form.user_name.data)
        project.update_now()
        db.session.add(project)
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for("project.project_view",
                                project_id=project.id))

    # Populate CSV fields
    if 'technai' in dir(form):
        form.technai.data = pack_csvlist(project.technai, ", ")
    if project.user:
        form.user_name.data = project.user.username

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
        flash('Project "%s" is now hidden.' % project.name, 'success')
    else:
        flash('Project "%s" is now visible.' % project.name, 'success')
    return redirect(url_for("admin.event_projects", event_id=project.event_id))


@blueprint.route('/project/<int:project_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def project_delete(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    if not project.is_hidden:
        flash('Project must be disabled.', 'warning')
    else:
        for a in project.activities:
            a.delete()
        project.delete()
        flash('Project deleted.', 'success')
    return redirect(url_for("admin.projects"))


@blueprint.route('/project/new', methods=['GET', 'POST'])
@login_required
@admin_required
def project_new():
    project = Project()
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.event_id.choices = [(e.id, e.name)
                             for e in Event.query.order_by(Event.id.desc())]
    current_event = Event.query.filter_by(is_current=True).first()

    # Set defaults and categories
    if current_event and not form.event_id.data:
        form.event_id.data = current_event.id
    if not form.technai.data:
        form.technai.data = ""
    form.category_id.choices = [(c.id, c.name)
                                for c in project.categories_all()]
    form.category_id.choices.insert(0, (-1, ''))

    if form.is_submitted() and form.validate():
        del form.id
        form.populate_obj(project)
        # TODO: this code is duplicated in project_edit
        # Ensure project category remains blank
        if project.category_id == -1:
            project.category_id = None
        # Assign technai from CSV
        project.technai = unpack_csvlist(form.technai.data)
        # Assign owner if selected
        project.user = get_user_by_name(form.user_name.data)
        project.update_now()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Project added.', 'success')
        return redirect(url_for("admin.event_projects",
                                event_id=project.event.id))
    if project.user:
        form.user_name.data = project.user.username
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
    return render_template('admin/categories.html', categories=categories,
                           active='categories')


@blueprint.route('/category/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    form = CategoryForm(obj=category, next=request.args.get('next'))
    form.event_id.choices = [(e.id, e.name)
                             for e in Event.query.order_by('name')]
    form.event_id.choices.insert(0, (-1, ''))

    if form.is_submitted() and form.validate():
        form.populate_obj(category)
        if category.event_id == -1:
            category.event_id = None
        if category.logo_color == '#000000':
            category.logo_color = ''

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
    form.event_id.choices = [(e.id, e.name)
                             for e in Event.query.order_by('name')]
    form.event_id.choices.insert(0, (-1, ''))

    if form.is_submitted() and form.validate():
        form.populate_obj(category)
        if category.event_id == -1:
            category.event_id = None

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
        flash('No projects may be assigned to category to delete.', 'warning')
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
    steps = getProjectStages()
    return render_template('admin/presets.html', categories=categories,
                           roles=roles, active='presets', steps=steps)


@blueprint.route('/role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def role(role_id):
    role = Role.query.filter_by(id=role_id).first_or_404()
    form = RoleForm(obj=role, next=request.args.get('next'))

    if form.is_submitted() and form.validate():
        form.populate_obj(role)

        db.session.add(role)
        db.session.commit()

        cache.clear()
        flash('Role updated.', 'success')
        return redirect(url_for("admin.presets"))

    return render_template(
            'admin/role.html',
            role=role, form=form, users=role.users[:50])


@blueprint.route('/role/new', methods=['GET', 'POST'])
@login_required
@admin_required
def role_new():
    role = Role()
    form = RoleForm(obj=role, next=request.args.get('next'))

    if form.is_submitted() and form.validate():
        del form.id
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
        flash('No users may be assigned to role to delete.', 'warning')
    else:
        cache.clear()
        role.delete()
        flash('Role deleted.', 'success')
    return redirect(url_for("admin.presets"))
