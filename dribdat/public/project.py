# -*- coding: utf-8 -*-
"""Views related to project management."""
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app, jsonify)
from flask_login import login_required, current_user

from dribdat.user.models import Event, Project
from dribdat.public.forms import (
    ProjectNew, ProjectForm, ProjectPost,
)
from dribdat.database import db
from dribdat.extensions import cache
from dribdat.aggregation import (
    SyncProjectData, GetProjectData,
    ProjectActivity, IsProjectStarred,
)
from dribdat.user import (
    projectProgressList, isUserActive,
)

blueprint = Blueprint('project', __name__, static_folder="../static", url_prefix='/project')

def current_event(): return Event.current()



@blueprint.route('/<int:project_id>')
def project_view(project_id):
    return project_action(project_id, None)

@blueprint.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (isUserActive(current_user) and current_user.is_admin)
    if not allow_edit:
        flash('You do not have access to edit this project.', 'warning')
        return project_action(project_id, None)
    form = ProjectForm(obj=project, next=request.args.get('next'))
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all()]
    if len(form.category_id.choices) > 0:
        form.category_id.choices.insert(0, (-1, ''))
    else:
        del form.category_id
    if form.validate_on_submit():
        del form.id
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Project updated.', 'success')
        project_action(project_id, 'update', False)
        return redirect(url_for('project.project_view', project_id=project.id))
    return render_template('public/projectedit.html',
        current_event=project.event, project=project, form=form)

@blueprint.route('/<int:project_id>/resource/add', methods=['GET', 'POST'])
@login_required
def resource_add(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (isUserActive(current_user) and current_user.is_admin)
    if not allow_edit:
        flash('You do not have access to add a resource.', 'warning')
        return project_action(project_id, None)
    resource = Resource()
    form = ResourceForm(obj=resource, next=request.args.get('next'))
    if form.validate_on_submit():
        del form.id
        form.populate_obj(resource)
        db.session.add(resource)
        db.session.commit()
        cache.clear()
        flash('Resource added.', 'success')
        # project_action(project_id, 'resource', False)
        return redirect(url_for('project.project_view', project_id=project.id))
    return render_template('public/resourcenew.html',
        current_event=project.event, project=project, resource=resource, form=form)

@blueprint.route('/<int:project_id>/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def resource_edit(project_id, resource_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    resource = Resource.query.filter_by(id=resource_id).first_or_404()
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (isUserActive(current_user) and current_user.is_admin)
    if not allow_edit:
        flash('You do not have access to edit this resource.', 'warning')
        return project_action(project_id, None)
    form = ResourceForm(obj=resource, next=request.args.get('next'))
    if form.validate_on_submit():
        del form.id
        form.populate_obj(resource)
        db.session.add(resource)
        db.session.commit()
        cache.clear()
        flash('Resource updated.', 'success')
        # project_action(project_id, 'resource', False)
        return redirect(url_for('project.project_view', project_id=project.id))
    return render_template('public/resourceedit.html',
        current_event=project.event, project=project, resource=resource, form=form)

@blueprint.route('/<int:project_id>/resource/<int:resource_id>/del', methods=['GET', 'POST'])
@login_required
def resource_delete(project_id, resource_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    resource = Resource.query.filter_by(id=resource_id).first_or_404()
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (isUserActive(current_user) and current_user.is_admin)
    if not allow_edit:
        flash('You do not have access to edit this resource.', 'warning')
        return project_action(project_id, None)
    resource.is_hidden = True
    db.session.add(resource)
    db.session.commit()
    flash('Resource removed.', 'success')
    # project_action(project_id, 'resource-removed', False)
    return redirect(url_for('project.project_view', project_id=project.id))

@blueprint.route('/<int:project_id>/post', methods=['GET', 'POST'])
@login_required
def project_post(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    starred = IsProjectStarred(project, current_user)
    allow_post = starred or (not current_user.is_anonymous and current_user.is_admin)
    # allow_post = allow_post and not event.lock_resources
    if not allow_post:
        flash('You do not have access to post to this project.', 'warning')
        return project_action(project_id, None)
    form = ProjectPost(obj=project, next=request.args.get('next'))

    # Evaluate project progress
    stage = project.stage
    all_valid = True
    project_data = project.data
    for v in stage['conditions']['validate']:
        v['valid'] = False
        vf = v['field']
        if vf in project_data:
            if ('min' in v and len(project_data[vf]) >= v['min']) or \
                ('max' in v and v['min'] <= len(project_data[vf]) <= v['max']) or \
                ('test' in v and v['test'] == 'validurl' and project_data[vf].startswith('http')):
                v['valid'] = True
        if not v['valid']:
            all_valid = False

    # Process form
    if form.validate_on_submit():

        # Check and update progress
        if form.has_progress.data:
            found_next = False
            if all_valid:
                for a in projectProgressList(True, False):
                    print(a[0])
                    if found_next:
                        project.progress = a[0]
                        flash('Your project has been promoted!', 'info')
                        break
                    if a[0] == project.progress or not project.progress or project.progress < 0:
                        found_next = True
                        print("Founddd")
            if not all_valid or not found_next:
                flash('Your project did not yet meet stage requirements.', 'info')

        # Update project data
        del form.id
        del form.has_progress
        form.populate_obj(project)
        project.update()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash('Thanks for your commit', 'success')
        project_action(project_id, 'update', action='post', text=form.note.data)
        # return redirect(url_for('project.project_view', project_id=project.id))
        return project_view(project.id)

    return render_template(
        'public/projectpost.html',
        current_event=event, project=project, form=form, stage=stage, all_valid=all_valid,
    )

def project_action(project_id, of_type=None, as_view=True, then_redirect=False, action=None, text=None):
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    if of_type is not None:
        ProjectActivity(project, of_type, current_user, action, text)
    if not as_view:
        return True
    if then_redirect:
        return redirect(url_for('project.project_view', project_id=project.id))
    starred = IsProjectStarred(project, current_user)
    allow_edit = starred or (not current_user.is_anonymous and current_user.is_admin)
    allow_post = allow_edit # and not event.lock_resources
    allow_edit = allow_edit and not event.lock_editing
    project_team = project.team()
    latest_activity = project.latest_activity()
    project_dribs = project.all_dribs()
    return render_template('public/project.html', current_event=event, project=project,
        project_starred=starred, project_team=project_team, project_dribs=project_dribs,
        allow_edit=allow_edit, allow_post=allow_post,
        # suggestions=suggestions, # TODO recommend similar projects
        latest_activity=latest_activity)

@blueprint.route('/<int:project_id>/star', methods=['GET', 'POST'])
@login_required
def project_star(project_id):
    if not isUserActive(current_user):
        return "User not allowed. Please contact event organizers."
    flash('Welcome to the team!', 'success')
    return project_action(project_id, 'star', then_redirect=True)

@blueprint.route('/<int:project_id>/unstar', methods=['GET', 'POST'])
@login_required
def project_unstar(project_id):
    flash('You have left the project', 'success')
    return project_action(project_id, 'unstar', then_redirect=True)

@blueprint.route('/event/<int:event_id>/project/new', methods=['GET', 'POST'])
@login_required
def project_new(event_id):
    if not isUserActive(current_user):
        flash("Your account needs to be activated: please contact an organizer.", 'warning')
        return redirect(url_for('public.event', event_id=event_id))
    form = None
    event = Event.query.filter_by(id=event_id).first_or_404()
    if event.lock_starting:
        flash('Starting a new project is disabled for this event.', 'error')
        return redirect(url_for('public.event', event_id=event.id))
    if isUserActive(current_user):
        project = Project()
        project.user_id = current_user.id
        form = ProjectNew(obj=project, next=request.args.get('next'))
        form.category_id.choices = [(c.id, c.name) for c in project.categories_all(event)]
        if len(form.category_id.choices) > 0:
            form.category_id.choices.insert(0, (-1, ''))
        else:
            del form.category_id
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
            if event.has_started:
                project_action(project.id, 'star', False) # Join team
            if len(project.autotext_url)>1:
                return project_autoupdate(project.id)
            else:
                return redirect(url_for('project.project_view', project_id=project.id))
    return render_template('public/projectnew.html', active="projectnew", current_event=event, form=form)

@blueprint.route('/<int:project_id>/autoupdate')
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
        flash("Could not sync: check that the Remote Link contains a README.", 'warning')
        return project_action(project_id)
    SyncProjectData(project, data)
    project_action(project.id, 'update', action='sync', text=str(len(project.autotext)) + ' bytes')
    flash("Project data synced from %s" % data['type'], 'success')
    return redirect(url_for('project.project_view', project_id=project.id))
