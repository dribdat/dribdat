# -*- coding: utf-8 -*-
"""Views related to project management."""

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
from dribdat.user.models import Event, Project, Activity, User
from dribdat.user.constants import drib_question
from dribdat.database import db
from dribdat.extensions import cache
from dribdat.utils import timesince, timelimit
from dribdat.public.forms import (
    ProjectImport,
    ProjectNew,
    ProjectPost,
    ProjectBoost,
    ProjectComment,
)
from dribdat.aggregation import (
    SyncProjectData,
    GetProjectData,
    AllowProjectEdit,
    IsProjectStarred,
    GetProjectACLs,
)
from dribdat.user import (
    validateProjectData,
    stageProjectToNext,
    isUserActive,
)
from dribdat.public.projhelper import (
    project_action,
    project_edit_action,
    templates_from_event,
    resources_by_stage,
    revert_project_by_activity,
    navigate_around_project,
    check_update,
)
from dribdat.apigenerate import gen_project_pitch, gen_project_post, prompt_ideas
from ..decorators import admin_required
from ..mailer import user_invitation


blueprint = Blueprint(
    "project", __name__, static_folder="../static", url_prefix="/project"
)


@blueprint.route("/<int:project_id>/")
@blueprint.route("/<int:project_id>")
def project_view(project_id):
    """Show a project by id."""
    return project_action(project_id, None)


@blueprint.route("/s/<project_name>")
def project_view_name(project_name):
    """Show a project matching by name."""
    project = Project.query.filter(Project.name.ilike(project_name)).first_or_404()
    return project_view(project.id)


@blueprint.route("/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(project_id):
    """Edit a project."""
    return project_edit_action(project_id)


@blueprint.route("/<int:project_id>/details", methods=["GET", "POST"])
@login_required
def project_details(project_id):
    """Edit a project's details."""
    return project_edit_action(project_id, True)


@blueprint.route("/<int:project_id>/boost", methods=["GET", "POST"])
@login_required
@admin_required
def project_boost(project_id):
    """Add a booster to a project."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event

    form = ProjectBoost(obj=project, next=request.args.get("next"))

    # TODO: load from a YAML file or from the Presets config
    form.boost_type.choices = [
        "---",
        "Award",
        "Qualified",
        "Top tutorial",
        "Data wizardry",
        "Awesome sauce",
        "People's choice",
        "Super committers",
        "Glorious purpose",
    ]

    # Process form
    if form.is_submitted() and form.validate():
        # Update project data
        cache.clear()
        project_action(
            project_id, "boost", action=form.boost_type.data, text=form.note.data
        )
        project.update_now()
        project.save()
        flash("Thanks for your boost!", "success")
        return project_view(project.id)

    return render_template(
        "public/projectboost.html",
        current_event=event,
        project=project,
        form=form,
        active="dribs",
    )


@blueprint.route("/<int:project_id>/autoboost", methods=["GET", "POST"])
@login_required
@admin_required
def project_autoboost(project_id):
    """Add automatic evaluation to a project."""
    p = Project.query.filter_by(id=project_id).first_or_404()
    # Go whizz up some content based on project data
    autopost = gen_project_post(p, True)
    if not autopost:
        flash("AI service is currently not available.", "warning")
        return redirect(url_for("project.get_log", project_id=p.id))
    # Save the new content in the project log
    project_action(p.id, "review", action="auto", text=autopost)
    flash("The robots have judged", "success")
    return redirect(url_for("project.get_log", project_id=p.id))


@blueprint.route("/<int:project_id>/approve", methods=["GET", "POST"])
@login_required
def project_approve(project_id):
    """Approve a challenge or promote project to next level."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    if not current_user.is_admin:
        if not current_user == project.event.user:
            flash("Permission denied", "danger")
            return redirect(url_for("public.event", event_id=project.event.id))

    # Update project
    if stageProjectToNext(project):
        project.update_now()
        db.session.add(project)
        db.session.commit()
        cache.clear()
        flash("Promoted to stage '%s'" % project.phase, "info")
    return redirect(url_for("project.project_view", project_id=project.id))


@blueprint.route("/<int:project_id>/render", methods=["GET"])
def render(project_id):
    """Transform project detail link."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    return render_template(
        "render.html", current_event=project.event, render_src=project.webpage_url
    )


@blueprint.route("/<int:project_id>/post", methods=["GET", "POST"])
@login_required
def project_post(project_id):
    """Add a Post to a project."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    allow_post = AllowProjectEdit(project, current_user)

    if not allow_post:
        flash("You do not have access to post to this project.", "warning")
        return redirect(url_for("project.project_view", project_id=project.id))

    if event.lock_resources:
        flash(
            "Comments are not available in the resource area. Please join a project.",
            "info",
        )
        return redirect(url_for("project.project_view", project_id=project.id))

    # Evaluate project progress
    stage, all_valid = validateProjectData(project)
    form = ProjectPost(obj=project, next=request.args.get("next"))

    # Apply random questions
    form.note.label.text = drib_question()

    # Quick hammer protection
    # TODO: currently OFF due to a TZ issue
    # thelastact = project.activities[-1].timestamp
    # if form.is_submitted() and timelimit(thelastact):
    #    flash("Please wait a minute before posting", 'warning')

    if form.is_submitted() and not form.note.data:
        # Empty submission
        flash("Please add something to your note", "warning")

    elif form.is_submitted() and form.validate():
        # Check and update progress
        if form.has_progress.data and all_valid:
            if stageProjectToNext(project):
                flash("Level up! You are at stage '%s'" % project.phase, "info")

        # Update project data
        del form.id
        del form.has_progress
        # Process form
        form.populate_obj(project)
        project.update_now()
        db.session.add(project)
        db.session.commit()
        cache.clear()

        # Write a post
        project_action(project_id, "update", action="post", text=form.note.data)
        flash("Thanks for sharing your progress!", "success")

        # Continue with project autoupdate
        if project.is_syncable and check_update(project, 10):
            project_autoupdate(project.id)
        return redirect(url_for("project.get_log", project_id=project.id))

    # Get latest written posts
    posts = project.all_dribs(5, None, True)

    return render_template(
        "public/projectpost.html",
        current_event=event,
        project=project,
        form=form,
        stage=stage,
        all_valid=all_valid,
        posts=posts,
        active="post",
    )


@blueprint.route("/<int:project_id>/comment", methods=["GET", "POST"])
@login_required
def project_comment(project_id):
    """Use Post as comments by non-team members."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    event = project.event
    form = ProjectComment(obj=project, next=request.args.get("next"))
    # Process form
    if form.is_submitted() and form.validate():
        # Update project data
        project_action(project_id, "review", action="post", text=form.note.data)

        flash("Thanks for your feedback!", "success")
        return redirect(url_for("project.get_log", project_id=project.id))

    # Get latest written posts
    posts = project.all_dribs(5, None, True)

    return render_template(
        "public/projectpost.html",
        current_event=event,
        project=project,
        form=form,
        posts=posts,
        active="dribs",
    )


@blueprint.route("/<int:project_id>/prompt", methods=["GET"])
@login_required
def project_autoprompt(project_id):
    """Share prompt for a project post."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    return prompt_ideas(project)


@blueprint.route("/<int:project_id>/auto", methods=["GET", "POST"])
@login_required
def project_autopost(project_id):
    """Try to generate a project post."""
    p = Project.query.filter_by(id=project_id).first_or_404()
    # Check if we've had some human contact, first
    # TODO: we may want to restrict this by time elapsed as well
    lastact = p.activities[-1]
    if lastact.content and "🅰️ℹ️" in lastact.content:
        flash(
            "Please write an update or commit before asking AI for more help.", "info"
        )
        return redirect(url_for("project.get_log", project_id=p.id))
    # Go whizz up some content based on project data
    autopost = gen_project_post(p)
    if not autopost:
        flash("AI service is currently not available.", "warning")
        return redirect(url_for("project.get_log", project_id=p.id))
    # Save the new content in the project log
    project_action(p.id, "review", action="auto", text=autopost)
    flash("The robots have spoken &#129302;", "success")
    return redirect(url_for("project.get_log", project_id=p.id))


@blueprint.route("/<int:project_id>/unpost/<int:activity_id>", methods=["GET"])
@login_required
def post_delete(project_id, activity_id):
    """Delete a Post."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    purl = url_for("project.get_log", project_id=project.id)
    activity = Activity.query.filter_by(id=activity_id).first_or_404()
    if not activity.may_delete(current_user):
        flash("No permission to delete.", "warning")
    else:
        activity.delete()
        flash("The post has been deleted.", "success")
    return redirect(purl)


@blueprint.route("/<int:project_id>/undo/<int:activity_id>", methods=["GET"])
@login_required
def post_revert(project_id, activity_id):
    """Revert project to a previous version."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    purl = url_for("project.project_view", project_id=project.id)
    if not AllowProjectEdit(project, current_user):
        flash("Could not revert: user not allowed.", "warning")
        return redirect(purl)
    activity = Activity.query.filter_by(id=activity_id).first_or_404()
    if not activity.project_version:
        flash("Could not revert: data not available.", "warning")
    elif activity.project_version == 0:
        flash("Could not revert: this is the earliest version.", "warning")
    else:
        revert_to = activity.project_version
        project.versions[revert_to].revert()
        project.save()
        flash("Project data reverted (version %d)." % revert_to, "success")
    return redirect(purl)


@blueprint.route("/<int:project_id>/preview/<int:activity_id>", methods=["GET"])
@login_required
def post_preview(project_id, activity_id):
    """Preview project data at a previous version."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    purl = url_for("project.get_log", project_id=project.id)
    activity = Activity.query.filter_by(id=activity_id).first_or_404()
    if not activity.project_version or activity.project_version == 0:
        flash("Could not preview.", "warning")
        return redirect(purl)
    preview_at = activity.project_version
    project = project.versions[preview_at]
    flash("This is an archived version (%d) of this project." % preview_at, "info")
    return render_template(
        "public/project.html",
        current_event=project.event,
        project=project,
        past_version=activity_id,
        allow_revert=True,
        active="projects",
    )


@blueprint.route("/<int:project_id>/challenge", methods=["GET"])
def get_challenge(project_id):
    """Preview project data at the previous version."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    purl = url_for("project.get_log", project_id=project.id)
    challenge = project.as_challenge()
    if not challenge:
        flash("Could not find challenge data.", "warning")
        return redirect(purl)
    preview_at = challenge.id
    p_date = timesince(challenge.updated_at)
    flash("This Challenge was posted %s" % p_date, "info")
    go_nav = navigate_around_project(project, True)
    return render_template(
        "public/project.html",
        project=challenge,
        go_nav=go_nav,
        challenge_when=p_date,
        current_event=challenge.event,
        active="projects",
    )


@blueprint.route("/<int:project_id>/log", methods=["GET"])
def get_log(project_id):
    """Show project log and report."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    project_dribs = project.all_dribs()
    # Get access settings
    starred = IsProjectStarred(project, current_user)
    allow_edit, allow_post, lock_editing = GetProjectACLs(
        current_user, project.event, starred
    )
    # Collect resource tips (from projects in a Template Event)
    suggestions = resources_by_stage(project.progress, 3)
    # Render the result
    return render_template(
        "public/projectlog.html",
        active="projects",
        project=project,
        current_event=project.event,
        project_dribs=project_dribs,
        project_starred=starred,
        allow_edit=allow_edit,
        allow_post=allow_post,
        lock_editing=lock_editing,
        suggestions=suggestions,
    )


@blueprint.route("/<int:project_id>/star/me", methods=["GET", "POST"])
@login_required
def project_star(project_id):
    """Join a project."""
    if not isUserActive(current_user):
        flash(
            "User currently not allowed to join projects - please contact "
            + " organizers for activation.",
            "warning",
        )
        return redirect(url_for("project.project_view", project_id=project_id))
    flash("Welcome to the team!", "success")
    return project_action(project_id, "star", then_redirect=True)


@blueprint.route("/<int:project_id>/star", methods=["POST"])
@login_required
def project_star_user(project_id):
    """Join a project by username (via form)."""
    username = request.form["username"].strip()
    if not username:
        flash("No data provided. Please try again.", "warning")
        return redirect(url_for("project.project_view", project_id=project_id))
    # Check permission first
    project = Project.query.filter_by(id=project_id).first_or_404()
    purl = url_for("project.project_view", project_id=project.id)
    if not AllowProjectEdit(project, current_user):
        flash("Could not invite: user not allowed.", "warning")
        return redirect(purl)
    if not "@" in username:
        # Search for a username
        user = User.query.filter(User.username.ilike(username)).first()
        if user is None:
            flash("User [%s] not found. Please try again." % username, "warning")
            return redirect(url_for("project.project_view", project_id=project_id))
        flash("Added %s to the team!" % username, "success")
        return project_action(project_id, "star", then_redirect=True, for_user=user)
    else:
        # Send an invite mail
        if user_invitation(username, project):
            flash("Invite has been sent!", "success")
            # Continue to project view
            return redirect(url_for("project.project_view", project_id=project.id))
        else:
            join_url = url_for(
                "project.project_star", project_id=project.id, _external=True
            )
            return redirect(
                "mailto:%s?subject=Invitation&body=%s" % (username, join_url)
            )


@blueprint.route("/<int:project_id>/unstar/me", methods=["GET", "POST"])
@login_required
def project_unstar_me(project_id):
    """Leave a project."""
    flash("You have left the project", "success")
    return project_action(project_id, "unstar", then_redirect=True)


@blueprint.route("/<int:project_id>/unstar/<int:user_id>", methods=["GET"])
@login_required
@admin_required
def project_unstar(project_id, user_id):
    """Kick a user from a project."""
    user = User.query.filter_by(id=user_id).first_or_404()
    project = Project.query.filter_by(id=project_id).first_or_404()
    if project.user == user:
        project.user = None
        project.save()
    flash("User %s has left the project" % user.username, "success")
    return project_action(project.id, "unstar", then_redirect=True, for_user=user)


@blueprint.route("/new/<int:event_id>", methods=["GET", "POST"])
def project_new(event_id):
    """If allowed to create a new project, do so."""

    is_anonymous = not current_user or current_user.is_anonymous
    if not is_anonymous and not isUserActive(current_user):
        flash(
            "Your account needs to be activated - " + " please contact an organizer.",
            "warning",
        )
        return redirect(url_for("public.event", event_id=event_id))
    elif is_anonymous:
        # You are not logged in, so your new project will be invisible until it is approved.
        pass
    event = Event.query.filter_by(id=event_id).first_or_404()
    if event.lock_starting:
        flash("Projects may not be started in this event.", "error")
        return redirect(url_for("public.event", event_id=event.id))
    # Checks passed, continue ...
    if is_anonymous or request.args.get("create"):
        return create_new_project(event, is_anonymous)
    # Only authenticated users can import due to autofill restrictions
    return import_new_project(event, is_anonymous)


def import_new_project(event, is_anonymous=False):
    """Proceed to import a new project."""

    form = None
    project = Project()

    if not is_anonymous:
        project.user_id = current_user.id
    else:
        project.hashtag = "Guest"
        project.is_hidden = True

    form = ProjectImport(obj=project, next=request.args.get("next"))

    if form.is_submitted() and not form.validate():
        print(form.errors)
        if "name" in form.errors and "unique" in form.errors["name"][0]:
            flash(
                "There is already a project with this name here. Please pick a new name, and add the Readme later.",
                "danger",
            )
            return redirect(
                url_for("project.project_new", event_id=event.id) + "?create=1"
            )
        else:
            flash(
                "Please use a supported site. Or just click the green button to skip this step.",
                "warning",
            )

    if not (form.is_submitted() and form.validate()):
        return render_template(
            "public/projectimport.html",
            current_event=event,
            form=form,
            active="projects",
        )

    # Process form result
    del form.id
    form.populate_obj(project)
    project.event_id = event.id
    if event.has_started:
        project.progress = 0
    else:
        project.progress = -1

    # Update the project
    project.update_now()
    db.session.add(project)
    db.session.commit()
    cache.clear()

    if is_anonymous:
        flash("Thanks for your submission - login and Join to make changes", "warning")
    else:
        flash("Invite your team to Join this page and contribute!", "success")
        project_action(project.id, "create", False)
        if not current_user.is_admin:
            project_action(project.id, "star", False)

    # Automatically sync data
    return project_autoupdate(project.id)


def create_new_project(event, is_anonymous=False):
    """Proceed to create a new project."""
    # Collect resource tips (from projects in a Template Event)
    suggestions = templates_from_event(event.lock_resources)

    # Project form
    form = None
    project = Project()

    if not is_anonymous:
        project.user_id = current_user.id
    else:
        project.hashtag = "Guest"
        project.is_hidden = True

    form = ProjectNew(obj=project, next=request.args.get("next"))

    # Add project categories
    form.category_id.choices = [(c.id, c.name) for c in project.categories_all(event)]
    if len(form.category_id.choices) > 0:
        form.category_id.choices.insert(0, (-1, ""))
    else:
        del form.category_id

    # If Captcha is not configured, skip the validation
    if not is_anonymous or not current_app.config["RECAPTCHA_PUBLIC_KEY"]:
        del form.recaptcha

    # Check if LLM support is configured
    if not current_app.config["LLM_API_KEY"]:
        del form.generate_pitch
    else:
        form.generate_pitch.label.text += (
            " using " + current_app.config["LLM_MODEL"].upper()
        )

    if not (form.is_submitted() and form.validate()):
        return render_template(
            "public/projectnew.html",
            current_event=event,
            form=form,
            suggestions=suggestions,
            active="projects",
        )

    # Process form result
    tpl_id = None
    if form.template.data:
        tpl_id = form.template.data
    del form.id
    del form.template
    form.populate_obj(project)

    # Apply template, if selected
    if tpl_id:
        template = Project.query.get(tpl_id)
        project.longtext = template.longtext
        project.image_url = template.image_url
        project.source_url = template.source_url
        project.webpage_url = template.webpage_url
        project.download_url = template.download_url

    project.event_id = event.id

    # Start as unapproved challenge
    project.progress = -1
    # Unless the event has started
    if event.has_started or event.lock_resources:
        project.progress = 0

    # Update the project
    project.update_now()

    # Magically populate description
    if form.generate_pitch and form.generate_pitch.data:
        project.longtext = gen_project_pitch(project)

    # Save to database
    db.session.add(project)
    db.session.commit()
    cache.clear()

    if is_anonymous:
        flash(
            "Thanks for your submission - log in and Join to make changes.", "success"
        )
    elif event.lock_resources:
        flash("Thanks for sharing a resource here!", "success")
    else:
        flash("Invite your team to Join this page and contribute!", "success")
        project_action(project.id, "create", False)
        # Automatically join new projects
        if not current_user.is_admin:
            project_action(project.id, "star", False)

    # Continue to project view
    purl = url_for("project.project_view", project_id=project.id)
    return redirect(purl)


@blueprint.route("/<int:project_id>/autoupdate")
@login_required
def project_autoupdate(project_id):
    """Sync remote project data."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    if not project.is_syncable:
        flash("This project is not syncable.", "warning")
        return redirect(url_for("project.project_view", project_id=project_id))

    # Check user permissions
    if not AllowProjectEdit(project, current_user):
        flash("You may not sync this project.", "warning")
        return redirect(url_for("project.project_view", project_id=project_id))

    # Check if we already have content
    has_autotext = project.autotext and len(project.autotext) > 1

    # Instruct user about certain links
    if project.autotext_url.startswith("https://docs.google.com/document") and (
        project.autotext_url.endswith("/edit") or "/edit#" in project.autotext_url
    ):
        flash("The Publish link should be used for a Google Doc", "warning")
        return redirect(url_for("project.project_view", project_id=project_id))

    # Start update process
    data = GetProjectData(project.autotext_url)
    if not data or "name" not in data:
        flash("To Sync: ensure a README on the remote site.", "warning")
        return redirect(url_for("project.project_view", project_id=project_id))

    # Transfer the project fields
    SyncProjectData(project, data)

    # Confirmation messages
    if project.autotext and len(project.autotext) > 1:
        project_action(
            project.id,
            "update",
            action="sync",
            text=str(len(project.autotext)) + " bytes",
        )
        if not has_autotext:
            flash("The latest data from %s has been synced." % data["type"], "dark")
        else:
            flash("Data from %s has been refreshed." % data["type"], "dark")
    else:
        flash("Could not sync: remote README is empty.", "warning")

    return redirect(url_for("project.project_view", project_id=project_id))


@blueprint.route("/<int:project_id>/toggle", methods=["GET", "POST"])
@login_required
def project_toggle(project_id):
    """Hide or unhide a project."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    purl = url_for("project.project_view", project_id=project.id)
    allow_toggle = AllowProjectEdit(project, current_user)
    if not allow_toggle:
        flash("You do not have permission to change visibility.", "warning")
        return redirect(purl)
    project.is_hidden = not project.is_hidden
    project.save()
    cache.clear()
    if project.is_hidden:
        flash('Project "%s" is now hidden.' % project.name, "success")
    else:
        flash('Project "%s" is now visible.' % project.name, "success")
    return redirect(purl)
