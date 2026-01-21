# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""

from dribdat.utils import load_event_presets
from flask import (
    Blueprint,
    request,
    render_template,
    flash,
    url_for,
    redirect,
    current_app,
)
from flask_login import login_required, current_user
from dribdat.user.models import User, Event, Project, Role
from dribdat.user import (
    getProjectStages, 
    isUserActive, USER_UNDER_REVIEW_MESSAGE,
)
from dribdat.public.userhelper import (
    get_users_by_search,
    get_dribs_paginated,
    get_contributor_stats,
)
from dribdat.public.forms import EventNew, EventEdit
from dribdat.public.projhelper import current_event
from dribdat.database import db
from dribdat.extensions import cache
from dribdat.aggregation import GetEventUsers
from urllib.parse import urlparse
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from dribdat.futures import UTC

# Set project version
VERSION = "0.9.3"

blueprint = Blueprint("public", __name__, static_folder="../static")

# Loads confiuration for events
EVENT_PRESET = load_event_presets()


@blueprint.route("/backboard/")
def backboard():
    """Render a static backboard. Better option."""
    event = current_event()
    if not event:
        return "No current event"
    if not current_app.config["BACKBOARD_URL"]:
        return "No Backboard service configured"
    url_event = url_for("api.package_current_event", format="json", _external=True)
    url_bb = current_app.config["BACKBOARD_URL"]
    if "?" in url_bb:
        url_bb = url_bb + "&src="
    else:
        url_bb = url_bb + "?src="
    return redirect(url_bb + url_event)


@blueprint.route("/dashboard/")
def dashboard():
    """Render a static dashboard. This code sucks."""
    event = current_event()
    if not event:
        return "No current event"
    wall_url = wall = None
    host = urlparse(event.community_url).hostname
    if (
        host == "mastodon.social"
    ):  # TODO: configure custom Mastodon provider via ENV-variable
        wall = "mastodon"
        userpart = event.community_url.split("/@")[-1]
        wall_url = (
            "https%3A%2F%2F%40"
            + userpart
            + "%40"
            + host
            + "%2Fusers%2F"
            + userpart.lower()
        )
    return render_template(
        "public/dashboard.html",
        current_event=event,
        with_social_wall=wall,
        wall_url=wall_url,
        status_text=event.status_text,
    )


@blueprint.route("/hackathon.json")
def info_current_hackathon_json():
    """Redirect to current event API."""
    return redirect(url_for("api.info_event_current_hackathon_json"))


@blueprint.route("/about/")
def about():
    """Render a static about page."""
    orgs = [u.data for u in User.query.filter_by(is_admin=True)]
    return render_template("public/about.html", active="about", orgs=orgs, ver=VERSION)


@blueprint.route("/terms/")
def terms():
    """Render a static terms of use page."""
    terms = EVENT_PRESET["terms"]
    return render_template("public/terms.html", active="terms", 
        current_event=current_event(), terms=terms)


@blueprint.route("/favicon.ico")
def favicon():
    """Favicon just points to a file."""
    return redirect(url_for("static", filename="img/favicon.ico"))


@blueprint.route("/")
def home():
    """Good old fashioned Home page."""
    cur_event = current_event()
    events = Event.query
    # Skip any hidden events
    events = events.filter(Event.is_hidden.isnot(True))
    # Query upcoming and past events which are not resource-typed
    timed_events = events.filter(Event.lock_resources.isnot(True)).order_by(
        Event.starts_at.desc()
    )
    events_featured = timed_events.filter(Event.is_current)
    # Filter out by today's date
    today = datetime.now(UTC)
    events_next = timed_events.filter(Event.ends_at > today)
    events_past = timed_events.filter(Event.ends_at < today)
    # Select Resource-type events
    resource_events = events.filter(Event.lock_resources)
    resource_events = resource_events.order_by(Event.name.asc())
    # Select my challenges
    my_projects = may_certify = None
    if current_user and not current_user.is_anonymous:
        my_projects = current_user.joined_projects(True, 3)
        if cur_event is not None:
            may_certify = cur_event.has_finished and cur_event.certificate_path
        if not isUserActive(current_user):
            flash(USER_UNDER_REVIEW_MESSAGE, "warning")
    # Filter past events
    MAX_PAST_EVENTS = 6
    events_past_next = events_past.count() > MAX_PAST_EVENTS
    events_past = events_past.limit(MAX_PAST_EVENTS)
    # Send to template
    return render_template(
        "public/home.html",
        active="home",
        featured_event=cur_event,
        events_featured=events_featured.all(),
        events_tips=resource_events.all(),
        events_next=events_next.all(),
        events_past=events_past.all(),
        events_past_next=events_past_next,
        my_projects=my_projects,
        may_certify=may_certify,
    )


@blueprint.route("/history")
def events_past():
    """List all past events."""
    # Skip any hidden events
    events = Event.query.filter(Event.is_hidden.isnot(True))
    # Query past events which are not resource-typed
    today = datetime.now(UTC)
    timed_events = events.filter(Event.lock_resources.isnot(True)).order_by(
        Event.starts_at.desc()
    )
    events_past = timed_events.filter(Event.ends_at < today)
    # Send to template
    return render_template(
        "public/history.html",
        active="history",
        events_past=events_past.all(),
        current_event=None,
    )


@blueprint.route("/user/<username>", methods=["GET"])
def user_profile(username):
    """Show a public user profile."""
    user = User.query.filter(
        func.lower(User.username) == func.lower(username)
    ).first_or_404()
    if not isUserActive(user):
        flash(USER_UNDER_REVIEW_MESSAGE, "warning")
        may_certify = False
    else:
        may_certify = (
            current_user
            and not current_user.is_anonymous
            and current_user.id == user.id
            and user.may_certify()[0]
        )
    # Check permissions ..
    is_current_user = (
        current_user
        and not current_user.is_anonymous
        and current_user.id == user.id
    )
    # Collect user data
    projects = user.joined_projects(False)
    posts = user.latest_posts(20)
    today = datetime.now(UTC)
    # Collect events
    events = []
    events_next = None
    if not projects:
        events_next = Event.query.filter(
            and_(
                Event.is_hidden.isnot(True),
                Event.lock_resources.isnot(True),
                Event.ends_at > today,
            )
        )
        events_next = events_next.order_by(Event.starts_at.desc())
        if events_next.count() == 0:
            events_next = None
    else:
        for p in projects:
            if p.event not in events:
                events.append(p.event)
    # Calculate score
    user_score = user.get_score()
    score_tip = int(user.get_profile_percent() * 100)
    # Parse the CV
    user_resume = user.simple_resume()
    # Filter out by today's date
    return render_template(
        "public/userprofile.html",
        active="profile",
        user=user,
        vitae=user_resume,
        projects=projects,
        posts=posts,
        score=user_score,
        score_tip=score_tip,
        events=events,
        events_next=events_next,
        may_certify=may_certify,
        is_current_user=is_current_user,
    )


@blueprint.route("/user", methods=["GET"])
@login_required
def user_current():
    """Redirect to the current user's profile."""
    return redirect(url_for("public.user_profile", username=current_user.username))


@blueprint.route("/user/_post", methods=["GET"])
@login_required
def user_post():
    """Redirect to a Post form for my current project."""
    projects = current_user.joined_projects(True, 1)
    if not len(projects) > 0:
        flash("Join a project to Post an update, or leave a Comment first.", "info")
        return redirect(url_for("public.home"))
    first_p = None
    for p in projects:
        if not p.is_hidden:
            first_p = p
            break
    if first_p is None:
        flash("Please wait for your challenge to be approved.", "info")
        return redirect(url_for("public.home"))
    if not p.event.has_started or p.event.has_finished:
        return redirect(url_for("project.project_comment", project_id=first_p.id))
    return redirect(url_for("project.project_post", project_id=first_p.id))


@blueprint.route("/user/_cert", methods=["GET"])
@login_required
def user_cert():
    """Download a user certificate."""
    status, why = current_user.may_certify()
    if status:
        # Proceed
        return redirect(why)
    if why == "projects":
        flash("Please Join your team project to get a certificate.", "info")
    elif why == "event":
        flash("A certificate is not yet available for this event.", "info")
    else:
        flash("Unknown error occurred.", "warning")
    return redirect(url_for("public.user_profile", username=current_user.username))


@blueprint.route("/event/<int:event_id>/")
@blueprint.route("/event/<int:event_id>")
def event(event_id):
    """Show an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    # Redirect resource type events
    if event.lock_resources:
        return event_resources(event_id)
    # Sort visible projects by identity (if used), or alphabetically
    projects = Project.query.filter_by(event_id=event_id, is_hidden=False)
    # Do not show unapproved challenges here
    projects = projects.filter(Project.progress >= 0)
    # Admin messages
    editable = False
    if current_user and not current_user.is_anonymous:
        # Set permission to edit the event
        editable = current_user.is_admin or event.user == current_user
        if not isUserActive(current_user):
            flash(USER_UNDER_REVIEW_MESSAGE, "warning")
    # Order by ident then name
    projects = projects.order_by(
        Project.ident, Project.name
    )
    # NB: the above must match projhelper->navigate_around_project
    # Embedding view
    if request.args.get("embed"):
        return render_template(
            "public/embed.html", current_event=event, projects=projects
        )
    # Trim instructions
    if event.instruction and '---' in event.instruction:
        event.instruction = event.instruction.split('---')[0]
    # Recommend projects
    summaries = []
    suggestions = []
    for project in projects:
        summaries.append(project.data)
        if project.needs_members:
            suggestions.append(project)
    # Check for certificate
    may_certify = event.has_finished and event.certificate_path
    if may_certify:
        may_certify = current_user and not current_user.is_anonymous
        may_certify = may_certify and current_user.may_certify()[0]
    # Generate the page
    return render_template(
        "public/event.html",
        current_event=event,
        may_certify=may_certify,
        may_edit=editable,
        summaries=summaries,
        project_count=len(summaries),
        suggestions=suggestions,
        active="projects",
    )


@blueprint.route("/event/<int:event_id>/participants")
def event_participants(event_id):
    """Show list of participants of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    users = GetEventUsers(event)
    preset_roles = Role.query.all()
    usercount = len(users) if users else 0
    return render_template(
        "public/eventusers.html",
        preset_roles=preset_roles,
        current_event=event,
        participants=users,
        usercount=usercount,
        active="people",
    )


@blueprint.route("/participants")
def all_participants():
    """Search for participants across events."""
    MAX_COUNT = 100
    search_by = request.args.get("u") or ""
    preset_roles = Role.query.all()
    if len(search_by) < 3:
        users = User.query.filter_by(active=True).all()
    else:
        users = get_users_by_search(search_by, MAX_COUNT)
    if len(users) == MAX_COUNT:
        flash("Only the first %d participants are shown." % MAX_COUNT, "info")
    usercount = len(users) if users else 0
    return render_template(
        "public/eventusers.html",
        u=search_by,
        preset_roles=preset_roles,
        participants=users,
        usercount=usercount,
        active="people",
    )


@blueprint.route("/event/<int:event_id>/stages")
def event_stages(event_id):
    """Show projects by stage for an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    steps = getProjectStages()
    for s in steps:
        s["projects"] = []  # Reset the index
    projects = Project.query.filter_by(event_id=event.id, is_hidden=False).order_by(
        Project.ident, Project.name
    )
    for s in steps:
        if "projects" not in s:
            s["projects"] = []
        project_list = []
        for p in projects.filter_by(progress=s["id"]).all():
            pp = p.data
            pp["stats"] = p.get_stats()
            pp["age"] = p.created_at
            project_list.append(pp)
        s["projects"].extend(project_list)
    return render_template(
        "public/eventstages.html", current_event=event, steps=steps, active="stages"
    )


@blueprint.route("/event/<int:event_id>/instruction")
def event_instruction(event_id):
    """Show instructions of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    return render_template(
        "public/eventinstruction.html",
        current_event=event,
        active="instruction",
    )


@blueprint.route("/event/<int:event_id>/categories")
def event_categories(event_id):
    """Show categories of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    steps = event.categories_for_event()
    projects = Project.query \
        .filter_by(event_id=event.id, is_hidden=False, category_id=None) \
        .order_by(Project.ident, Project.name) \
        .all()
    return render_template(
        "public/eventcategories.html",
        current_event=event,
        steps=steps,
        projects=projects,
        active="categories",
    )


@blueprint.route("/event/<int:event_id>/challenges")
def event_challenges(event_id):
    """Show all the challenges of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query \
        .filter_by(event_id=event.id, is_hidden=False)
    if 'all' not in request.args:
        projects = projects.filter(Project.progress >= 0)
    projects = projects.order_by(
            Project.ident, Project.name
        )
    challenges = [p.as_challenge() for p in projects]
    return render_template(
        "public/eventchallenges.html",
        current_event=event,
        projects=challenges,
        project_count=projects.count(),
        active="challenges",
    )


@blueprint.route("/event/<int:event_id>/resources")
def event_resources(event_id):
    """Show the resources view of an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    projects = Project.query.filter_by(event_id=event.id, is_hidden=False).order_by(
        Project.ident, Project.progress, Project.name
    )
    return render_template(
        "public/eventresources.html",
        current_event=event,
        projects=projects,
        project_count=projects.count(),
        active="resources",
    )


@blueprint.route("/event/<int:event_id>/print")
def event_print(event_id):
    """Print the results of an event."""
    now = datetime.now(UTC).strftime("%d.%m.%Y %H:%M")
    event = Event.query.filter_by(id=event_id).first_or_404()
    eventdata = Project.query.filter_by(event_id=event_id, is_hidden=False)
    projects = eventdata.filter(Project.progress > 0).order_by(
        Project.ident, Project.name
    )
    challenges = eventdata.filter(Project.progress == 0).order_by(
        Project.ident, Project.name
    )
    return render_template(
        "public/eventprint.html",
        active="print",
        projects=projects,
        challenges=challenges,
        current_event=event,
        curdate=now,
    )


@blueprint.route("/event/start", methods=["GET"])
@login_required
def event_start():
    """Guidelines for new events."""
    if not current_app.config["DRIBDAT_ALLOW_EVENTS"]:
        if not current_user.is_admin:
            flash("Only administrators may start events here.", "danger")
            return redirect(url_for("public.home"))
    tips = EVENT_PRESET["eventstart"]
    return render_template("public/eventstart.html", tips=tips)


@blueprint.route("/event/new", methods=["GET", "POST"])
@login_required
def event_new():
    """Start a new event."""
    if not current_app.config["DRIBDAT_ALLOW_EVENTS"]:
        if not current_user.is_admin:
            return redirect(url_for("public.event_start"))
    event = Event()
    event.starts_at = (datetime.now(UTC) + timedelta(days=1)).replace(
        hour=9, minute=00, second=00
    )
    event.ends_at = (event.starts_at + timedelta(days=1)).replace(hour=16)
    form = EventNew(obj=event, next=request.args.get("next"))
    if form.is_submitted() and form.validate():
        # Check event dates
        if not form.starts_at.data < form.ends_at.data:
            flash("Please check Starting and Finishing dates", "warning")
        else:
            # Save event data
            del form.id
            form.populate_obj(event)
            # Load default event content
            event.user_id = current_user.id
            event.boilerplate = EVENT_PRESET["quickstart"]
            event.community_embed = EVENT_PRESET["codeofconduct"]
            db.session.add(event)
            db.session.commit()
            if not current_user.is_admin:
                event.is_hidden = True
                event.save()
                flash(
                    "Please contact an administrator (see About page)"
                    + "to make changes or to promote this event.",
                    "warning",
                )
            else:
                flash("A new event has been planned!", "success")
            cache.clear()
            return redirect(url_for("public.event", event_id=event.id))
    if not current_user.is_admin:
        flash(
            "An administrator can make your new event visible on the home page.", "info"
        )
    return render_template("public/eventnew.html", form=form, active="Event")


@blueprint.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def event_edit(event_id):
    event = Event.query.filter_by(id=event_id).first_or_404()

    if not current_user.is_admin and not event.user == current_user:
        flash("Only admins and event owners are allowed to edit.")
        return redirect(url_for("public.event", event_id=event.id))

    if event.location_lat is None or event.location_lon is None:
        event.location_lat = event.location_lon = 0

    form = EventEdit(obj=event, next=request.args.get("next"))

    if form.is_submitted() and form.validate():
        form.populate_obj(event)
        event.starts_at = datetime.combine(form.starts_date.data, form.starts_time.data)
        event.ends_at = datetime.combine(form.ends_date.data, form.ends_time.data)

        db.session.add(event)
        db.session.commit()

        cache.clear()

        flash("Saved your event.", "success")
        return redirect(url_for("public.event", event_id=event.id))

    form.starts_date.data = event.starts_at
    form.starts_time.data = event.starts_at
    form.ends_date.data = event.ends_at
    form.ends_time.data = event.ends_at
    return render_template("public/eventedit.html", event=event, form=form)


#####


@blueprint.route("/clear/cache", methods=["GET"])
@login_required
def clear_cache():
    """Clear the site cache."""
    flash("Show me the cache!", "success")
    cache.clear()
    return redirect(url_for("public.home"))


@blueprint.route("/dribs")
def dribs():
    """Show the latest logged posts."""
    page = int(request.args.get("page") or 1)
    per_page = int(request.args.get("limit") or 10)
    dribs = get_dribs_paginated(page, per_page, request.host_url)
    stats = get_contributor_stats()
    return render_template(
        "public/dribs.html",
        current_event=current_event(),
        endpoint="public.dribs",
        active="dribs",
        data=dribs,
        stats=stats,
    )
