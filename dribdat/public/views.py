# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from dribdat.utils import load_event_presets
from flask import (Blueprint, request, render_template, flash, url_for,
                   redirect, current_app, jsonify)
from flask_login import login_required, current_user

from dribdat.user.models import User, Event, Project, Activity
from dribdat.public.forms import NewEventForm
from dribdat.database import db
from dribdat.extensions import cache
from dribdat.aggregation import GetEventUsers
from dribdat.user import getProjectStages, isUserActive

from datetime import datetime

blueprint = Blueprint('public', __name__, static_folder="../static")


EVENT_PRESET = load_event_presets()


def current_event(): return Event.current()


@blueprint.route("/dashboard/")
def dashboard():
    """ Renders a static dashboard """
    event = current_event()
    if not event:
        return 'No current event'
    wall = 'twitter.com' in event.community_url
    return render_template(
        "public/dashboard.html",
        current_event=event, with_social_wall=wall
    )


@blueprint.route('/hackathon.json')
def info_current_hackathon_json():
    """ Outputs JSON-LD about the current event """
    # (see also api.py/info_event_hackathon_json)
    event = Event.query.filter_by(is_current=True).first(
    ) or Event.query.order_by(Event.id.desc()).first()
    return jsonify(event.get_schema(request.host_url))


@blueprint.route("/about/")
def about():
    """ Renders a simple about page """
    return render_template("public/about.html", current_event=current_event())


@blueprint.route("/favicon.ico")
def favicon():
    """ Favicon just points to a file """
    return redirect(url_for('static', filename='img/favicon.ico'))


@blueprint.route("/")
def home():
    """ Home page """
    cur_event = current_event()
    if cur_event is not None:
        events = Event.query.filter(Event.id != cur_event.id)
    else:
        events = Event.query
    # Skip any hidden events
    events = events.filter(Event.is_hidden.isnot(True))
    # Query upcoming and past events which are not resource-typed
    today = datetime.utcnow()
    timed_events = events.filter(Event.lock_resources.isnot(
        True)).order_by(Event.starts_at.desc())
    today = datetime.utcnow()
    events_next = timed_events.filter(Event.starts_at > today).all()
    events_past = timed_events.filter(Event.ends_at < today).all()
    # Select a featured event if none is selected
    if cur_event is None:
        events_now = timed_events.filter(
            Event.starts_at <= today).filter(Event.ends_at >= today)
        cur_event = events_now.first()
    # Select Resource-type events
    resource_events = events.filter(
        Event.lock_resources).order_by(Event.name.asc()).all()
    # Send to template
    return render_template("public/home.html",
                           events_next=events_next, events_past=events_past,
                           events_tips=resource_events,
                           current_event=cur_event)


@blueprint.route('/user/<username>', methods=['GET'])
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not isUserActive(user):
        # return "User deactivated. Please contact an event organizer."
        flash('This user account is under review. Please contact the organizing team if you have any questions.', 'warning')
    event = current_event()
    cert_path = user.get_cert_path(event)
    submissions = user.posted_challenges()
    projects = user.joined_projects(False)
    posts = user.latest_posts()
    return render_template("public/userprofile.html", active="profile",
                           current_event=event, event=event, user=user, cert_path=cert_path,
                           projects=projects, submissions=submissions, posts=posts)


@blueprint.route("/event/<int:event_id>")
def event(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    if request.args.get('embed'):
        return render_template("public/embed.html", current_event=event, projects=projects)
    summaries = [p.data for p in projects]
    # Sort projects by reverse score, then name
    summaries.sort(key=lambda x: (
        -x['score'] if isinstance(x['score'], int) else 0,
        x['name'].lower()))
    project_count = projects.count()
    return render_template("public/event.html", current_event=event,
                           projects=summaries, project_count=project_count, active="projects")


@blueprint.route("/event/<int:event_id>/participants")
def event_participants(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    users = GetEventUsers(event)
    usercount = len(users) if users else 0
    return render_template("public/eventusers.html",
                           current_event=event, participants=users, usercount=usercount, active="participants")


@blueprint.route("/event/<int:event_id>/stages")
def event_stages(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    steps = getProjectStages()
    return render_template("public/stages.html",
                           current_event=event, steps=steps, active="stages")


@blueprint.route("/event/<int:event_id>/instruction")
def event_instruction(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()
    steps = getProjectStages()
    for s in steps:
        s['projects'] = []  # Reset the index
    resource_events = Event.query.filter_by(lock_resources=True).all()
    for e in resource_events:
        projects = Project.query.filter_by(event_id=e.id, is_hidden=False)
        for s in steps:
            if not 'projects' in s:
                s['projects'] = []
            project_list = [p.data for p in projects.filter_by(
                progress=s['id']).all()]
            s['projects'].extend(project_list)
    return render_template("public/instruction.html",
                           current_event=event, steps=steps, active="instruction")


@blueprint.route('/event/<int:event_id>/print')
def event_print(event_id):
    now = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    projects = projects.filter(Project.progress >= 0).order_by(Project.name)
    return render_template('public/eventprint.html',
                           current_event=event, projects=projects, curdate=now, active='print')


@blueprint.route('/event/start', methods=['GET'])
@login_required
def event_start():
    if not current_app.config['DRIBDAT_ALLOW_EVENTS'] and not current_user.is_admin:
        flash('Only administrators can start events on this server.', 'danger')
    tips = EVENT_PRESET['eventstart']
    return render_template('public/eventstart.html', tips=tips)


@blueprint.route('/event/new', methods=['GET', 'POST'])
@login_required
def event_new():
    if not current_app.config['DRIBDAT_ALLOW_EVENTS'] and not current_user.is_admin:
        return redirect(url_for("public.event_start"))
    event = Event()
    form = NewEventForm(obj=event, next=request.args.get('next'))
    if form.validate_on_submit():
        del form.id
        form.populate_obj(event)
        event.starts_at = datetime.combine(
            form.starts_date.data, form.starts_time.data)
        event.ends_at = datetime.combine(
            form.ends_date.data, form.ends_time.data)
        # Load default event content
        event.boilerplate = EVENT_PRESET['quickstart']
        event.community_embed = EVENT_PRESET['codeofconduct']
        event.is_hidden = True
        db.session.add(event)
        db.session.commit()
        flash('A new event has been planned!', 'success')
        if not current_user.is_admin:
            flash(
                'Please contact an administrator to make changes and promote this event.', 'warning')
        cache.clear()
        return redirect(url_for("public.event", event_id=event.id))
    return render_template('public/eventnew.html', form=form)

#####


@blueprint.route("/dribs")
def dribs():
    """ Shows the latest logged posts """
    page = request.args.get('page') or 1
    per_page = request.args.get('limit') or 10
    dribs = Activity.query.filter(Activity.action == "post")
    dribs = dribs.order_by(Activity.id.desc())
    dribs = dribs.paginate(int(page), int(per_page))
    return render_template("public/dribs.html",
                           endpoint='public.dribs', active='dribs',
                           current_event=current_event(), data=dribs)
