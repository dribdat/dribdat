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
from urllib.parse import quote, quote_plus, urlparse
from datetime import datetime
from sqlalchemy import and_, or_
import re

blueprint = Blueprint('public', __name__, static_folder="../static")

# Loads confiuration for events
EVENT_PRESET = load_event_presets()

# Removes markdown and HTML tags
RE_NO_TAGS = re.compile(r'\!\[[^\]]*\]\([^\)]+\)|\[|\]|<[^>]+>')


def current_event():
    """Just get a current event."""
    return Event.current()


@blueprint.route("/dashboard/")
def dashboard():
    """Render a static dashboard. This code sucks."""
    event = current_event()
    if not event:
        return 'No current event'
    wall_url = wall = None
    social_domains = ['twitter.com']
    host = urlparse(event.community_url).hostname
    if host == 'twitter.com' or host == 'mobile.twitter.com':
        wall = 'twitter'
        wall_url = event.community_url + '?ref_src=twsrc%5Etfw'
    elif host == 'mastodon.social': # TODO: configure custom Mastodon provider via ENV-variable
        wall = 'mastodon'
        userpart = event.community_url.split('/@')[-1]
        wall_url = 'https%3A%2F%2F%40' + userpart + '%40' + host + '%2Fusers%2F' + userpart.lower()
    return render_template(
        "public/dashboard.html",
        current_event=event, with_social_wall=wall, wall_url=wall_url, status_text=event.status_text
    )


@blueprint.route('/hackathon.json')
def info_current_hackathon_json():
    """Output JSON-LD about the current event."""
    # (see also api.py/info_event_hackathon_json)
    event = Event.query.filter_by(is_current=True).first(
    ) or Event.query.order_by(Event.id.desc()).first()
    return jsonify(event.get_schema(request.host_url))


@blueprint.route("/about/")
def about():
    """Render a static about page."""
    orgs = [u.data for u in User.query.filter_by(is_admin=True)]
    return render_template("public/about.html", active="about", orgs=orgs)


@blueprint.route("/favicon.ico")
def favicon():
    """Favicon just points to a file."""
    return redirect(url_for('static', filename='img/favicon.ico'))


@blueprint.route("/")
def home():
    """Home page."""
    cur_event = current_event()
    if cur_event is not None:
        events = Event.query.filter(Event.id != cur_event.id)
    else:
        events = Event.query
    # Skip any hidden events
    events = events.filter(Event.is_hidden.isnot(True))
    # Query upcoming and past events which are not resource-typed
    timed_events = events.filter(Event.lock_resources.isnot(
        True)).order_by(Event.starts_at.desc())
    # Filter out by today's date
    today = datetime.utcnow()
    events_next = timed_events.filter(Event.ends_at > today)
    events_featured = events_next.filter(Event.is_current)
    events_past = timed_events.filter(Event.ends_at < today)
    # Select Resource-type events
    resource_events = events.filter(Event.lock_resources)
    resource_events = resource_events.order_by(Event.name.asc())
    # Select my challenges
    my_projects = None
    if current_user and not current_user.is_anonymous:
        my_projects = current_user.joined_projects(True, 3)
    # Filter past events
    MAX_PAST_EVENTS = 6
    events_past_next = events_past.count() > MAX_PAST_EVENTS
    events_past = events_past.limit(MAX_PAST_EVENTS)
    # Send to template
    return render_template("public/home.html", active="home",
                           events_featured=events_featured.all(),
                           events_tips=resource_events.all(),
                           events_next=events_next.all(),
                           events_past=events_past.all(),
                           events_past_next=events_past_next,
                           my_projects=my_projects,
                           current_event=cur_event)


@blueprint.route("/history")
def events_past():
    """List all past events."""
    # Skip any hidden events
    events = Event.query.filter(Event.is_hidden.isnot(True))
    # Query past events which are not resource-typed
    today = datetime.utcnow()
    timed_events = events.filter(Event.lock_resources.isnot(
        True)).order_by(Event.starts_at.desc())
    events_past = timed_events.filter(Event.ends_at < today)
    # Send to template
    return render_template("public/history.html", active="history",
                           events_past=events_past.all(),
                           current_event=None)


@blueprint.route('/user/<username>', methods=['GET'])
def user(username):
    """Show a user profile."""
    user = User.query.filter_by(username=username).first_or_404()
    # logged_in = current_user and not current_user.is_anonymous
    if not isUserActive(user):
        flash(
            'User account is under review. Please contact the '
            + 'organizing team for full access.',
            'info'
        )
    submissions = user.posted_challenges()
    projects = user.joined_projects(True)
    posts = user.latest_posts(20)
    today = datetime.utcnow()
    events_next = Event.query.filter(and_(
        Event.is_hidden.isnot(True),
        Event.lock_resources.isnot(True),
        Event.ends_at > today
    ))
    events_next = events_next.order_by(Event.starts_at.desc())
    if events_next.count() == 0: events_next = None
    # Filter out by today's date
    return render_template("public/userprofile.html", active="profile",
                           user=user, projects=projects, posts=posts,
                           events_next=events_next,
                           score=user.get_score(),
                           submissions=submissions,
                           may_certify=user.may_certify()[0])


@blueprint.route('/user/_post', methods=['GET'])
@login_required
def user_post():
    """Redirect to a Post form for my current project."""
    projects = current_user.joined_projects(True, 1)
    if not len(projects) > 0:
        flash('Please Join a project to be able to Post an update.', 'info')
        return redirect(url_for("public.home"))
    return redirect(url_for("project.project_post", project_id=projects[0].id))


@blueprint.route('/user/_cert', methods=['GET'])
@login_required
def user_cert():
    """Download a user certificate."""
    status, why = current_user.may_certify()
    if status:
        # Proceed
        return redirect(why)
    if why == 'projects':
        flash('Please Join your team project to get a certificate.', 'info')
    elif why == 'event':
        flash('A certificate is not yet available for this event.', 'info')
    else:
        flash('Unknown error occurred.', 'warning')
    return redirect(url_for("public.user", username=current_user.username))


@blueprint.route("/event/<int:event_id>/")
@blueprint.route("/event/<int:event_id>")
def event(event_id):
    """Show an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    # Sort visible projects by reverse score, then name
    projects = Project.query \
        .filter_by(event_id=event_id, is_hidden=False) \
        .order_by(Project.score.desc(), Project.ident, Project.name)
        # The above must match projhelper->navigate_around_project
    # Embedding view
    if request.args.get('embed'):
        return render_template("public/embed.html",
                               current_event=event, projects=projects)
    # TODO: seems inefficient? We only need a subset of the data here:
    summaries = [ p.data for p in projects ]
    return render_template("public/event.html", current_event=event,
                           summaries=summaries, project_count=len(summaries),
                           active="projects")


@blueprint.route("/event/<int:event_id>/participants")
def event_participants(event_id):
    """Show list of participants of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    users = GetEventUsers(event)
    cert_path = None
    search_by = request.args.get('q') or ''
    role_call = request.args.get('r') or ''
    # Quick (actually, rather slow..) search filter
    if role_call and len(role_call) > 2:
        usearch = []
        for u in users:
            for r in u.roles:
                if role_call in str(r):
                    usearch.append(u)
                    search_by = role_call
                    break
    elif search_by and len(search_by) > 2:
        usearch = []
        qq = search_by.replace('@', '').lower()
        for u in users:
            if qq in u.username.lower() or qq in u.email.lower():
                usearch.append(u)
            elif (u.my_story and qq in u.my_story.lower()) or \
                 (u.my_goals and qq in u.my_goals.lower()):
                usearch.append(u)
    else:
        usearch = users
        search_by = ''
    # Provide certificate if available
    if current_user and not current_user.is_anonymous:
        cert_path = current_user.get_cert_path(event)
    usercount = len(usearch) if usearch else 0
    return render_template("public/eventusers.html",
                           q=search_by,
                           cert_path=cert_path,
                           current_event=event, participants=usearch,
                           usercount=usercount, active="participants")



@blueprint.route("/participants")
def all_participants():
    """Show list of participants of an event."""
    users = User.query.filter_by(active=True)
    search_by = request.args.get('q')
    if search_by and len(search_by) > 2:
        q = search_by.replace('@', '').lower()
        q = "%%%s%%" % q
        if '@' in search_by:
            users = users.filter(or_(
                User.email.ilike(q),
                User.username.ilike(q)
            ))
        else:
            users = users.filter(or_(
                User.my_story.ilike(q),
                User.my_goals.ilike(q),
            ))
    else:
        users = users.limit(50).all()
        search_by = ''
    # Provide certificate if available
    if users:
        users = sorted(users, key=lambda x: x.username)
        usercount = len(users)
    else:
        usercount = 0
    return render_template("public/eventusers.html",
                           q=search_by,
                           participants=users, 
                           usercount=usercount, 
                           active="participants")


@blueprint.route("/event/<int:event_id>/stages")
def event_stages(event_id):
    """Show projects by stage for an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    steps = getProjectStages()
    for s in steps:
        s['projects'] = []  # Reset the index
    projects = Project.query.filter_by(event_id=event.id, is_hidden=False) \
                            .order_by(Project.ident, Project.name)
    for s in steps:
        if 'projects' not in s:
            s['projects'] = []
        project_list = [p.data for p in projects.filter_by(
            progress=s['id']).all()]
        s['projects'].extend(project_list)
    return render_template("public/eventstages.html",
                           current_event=event, steps=steps, active="stages")


@blueprint.route("/event/<int:event_id>/instruction")
def event_instruction(event_id):
    """Show instructions of an event."""
    # Deprecated (for now)
    return redirect(url_for("public.event_stages", event_id=event_id))


@blueprint.route("/event/<int:event_id>/categories")
def event_categories(event_id):
    """Show categories of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    steps = event.categories_for_event()
    projects = Project.query.filter_by(event_id=event.id, is_hidden=False)
    projects = projects.filter_by(category_id=None)
    return render_template("public/eventcategories.html",
                           current_event=event, steps=steps, projects=projects,
                           active="categories")


@blueprint.route("/event/<int:event_id>/challenges")
def event_challenges(event_id):
    """Show all the challenges of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event.id, is_hidden=False) \
                            .order_by(Project.ident, Project.name)
    if not current_user or current_user.is_anonymous or not current_user.is_admin:
        projects = projects.filter(Project.progress >= 0)
    challenges = [ p.as_challenge() for p in projects ]
    return render_template("public/eventchallenges.html", 
                           current_event=event, projects=challenges, 
                           project_count=projects.count(),
                           active="challenges")


@blueprint.route('/event/<int:event_id>/print')
def event_print(event_id):
    """Print the results of an event."""
    now = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    event = Event.query.filter_by(id=event_id).first_or_404()
    eventdata = Project.query.filter_by(event_id=event_id, is_hidden=False)
    projects = eventdata.filter(Project.progress > 0).order_by(Project.ident, Project.name)
    challenges = eventdata.filter(Project.progress == 0).order_by(Project.ident, Project.name)
    return render_template('public/eventprint.html', active='print',
                           projects=projects, challenges=challenges,
                           current_event=event, curdate=now)


@blueprint.route('/event/start', methods=['GET'])
@login_required
def event_start():
    """Guidelines for new events."""
    if not current_app.config['DRIBDAT_ALLOW_EVENTS']:
        if not current_user.is_admin:
            flash('Only administrators may start events here.', 'danger')
            return redirect(url_for("public.home"))
    tips = EVENT_PRESET['eventstart']
    return render_template('public/eventstart.html', tips=tips)


@blueprint.route('/event/new', methods=['GET', 'POST'])
@login_required
def event_new():
    """Start a new event."""
    if not current_app.config['DRIBDAT_ALLOW_EVENTS']:
        if not current_user.is_admin:
            return redirect(url_for("public.event_start"))
    event = Event()
    form = NewEventForm(obj=event, next=request.args.get('next'))
    if form.is_submitted() and form.validate():
        del form.id
        form.populate_obj(event)
        event.starts_at = datetime.combine(
            form.starts_date.data, form.starts_time.data)
        event.ends_at = datetime.combine(
            form.ends_date.data, form.ends_time.data)
        # Load default event content
        event.boilerplate = EVENT_PRESET['quickstart']
        event.community_embed = EVENT_PRESET['codeofconduct']
        db.session.add(event)
        db.session.commit()
        if not current_user.is_admin:
            event.is_hidden = True
            event.save()
            flash(
                'Please contact an administrator (see About page)'
                + 'to make changes or to promote this event.',
                'warning')
        else:
            flash('A new event has been planned!', 'success')
        cache.clear()
        return redirect(url_for("public.event", event_id=event.id))
    if not current_user.is_admin:
        flash('An administrator can make your new event visible on the home page.',
                'info')
    return render_template('public/eventnew.html', form=form, active='Event')

#####


@blueprint.route('/clear/cache', methods=['GET'])
@login_required
def clear_cache():
    """Clear the site cache."""
    flash('Show me the cache!', 'success')
    cache.clear()
    return redirect(url_for("public.home"))


@blueprint.route("/dribs")
def dribs():
    """Show the latest logged posts."""
    page = int(request.args.get('page') or 1)
    per_page = int(request.args.get('limit') or 10)
    latest_dribs = Activity.query.filter(or_(
        Activity.action == "post",
        Activity.name == "boost")).order_by(Activity.id.desc())
    dribs = latest_dribs.paginate(page=page, per_page=per_page)
    dribs.items = [
        d for d in dribs.items
        if not d.project.is_hidden and d.content]
    # Generate social links
    for d in dribs.items:
        d.share = {
            'text': quote(" ".join([
                RE_NO_TAGS.sub('', d.content or d.project.name),
                d.project.event.hashtags or '#dribdat']).strip()),
            'url': quote_plus(request.host_url + d.project.url)
        }
    return render_template("public/dribs.html",
                           current_event=current_event(),
                           endpoint='public.dribs', active='dribs', 
                           data=dribs)
