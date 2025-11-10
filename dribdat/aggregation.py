# -*- coding: utf-8 -*-
"""Utilities for aggregating data."""

import re
import json
from dribdat.user.models import Activity, User, Project
from dribdat.user import isUserActive
from dribdat.database import db
from dribdat.api.parser import GetProjectData
from sqlalchemy import and_
from requests.exceptions import ConnectionError
from flask import flash, redirect, url_for


def TrimProjectData(project, data):
    """Map remote fields to project data."""
    if len(data["name"]) > 0:
        project.name = data["name"][0:80]
    if "ident" in data and len(data["ident"]) > 0:
        project.ident = data["ident"][0:10]
    if "hashtag" in data and len(data["hashtag"]) > 0:
        project.hashtag = data["hashtag"][0:140]
    if "summary" in data and len(data["summary"]) > 0:
        project.summary = data["summary"][0:2048]
    if "description" in data and len(data["description"]) > 0:
        project.longtext = data["description"]
    if "source_url" in data and len(data["source_url"]) > 0:
        project.source_url = data["source_url"][0:2048]
    if "webpage_url" in data and len(data["webpage_url"]) > 0:
        project.webpage_url = data["webpage_url"][0:2048]
    if "contact_url" in data and len(data["contact_url"]) > 0:
        project.contact_url = data["contact_url"][0:2048]
    if "download_url" in data and len(data["download_url"]) > 0:
        project.download_url = data["download_url"][0:2048]
    if "image_url" in data and len(data["image_url"]) > 0:
        project.image_url = data["image_url"][0:2048]
    if "logo_icon" in data and len(data["logo_icon"]) > 0:
        project.logo_icon = data["logo_icon"][0:40]


def SyncProjectData(project, data):
    """Sync remote project data."""
    # Yes, the function above looks very similar to this one.
    # However, here we only overwrite the fields that are new.
    # DRY improvements are possible though..
    # Always update "autotext" field
    if "description" in data and data["description"]:
        project.autotext = data["description"]
    # Update following fields only if blank
    if (
        "name" in data
        and data["name"]
        and (not project.name or not project.name.strip())
    ):
        project.name = data["name"][:80]
    if (
        "ident" in data
        and data["ident"]
        and (not project.ident or not project.ident.strip())
    ):
        project.ident = data["ident"][:10]
    if (
        "hashtag" in data
        and data["hashtag"]
        and (not project.hashtag or not project.hashtag.strip())
    ):
        project.hashtag = data["hashtag"][:140]
    if (
        "summary" in data
        and data["summary"]
        and (not project.summary or not project.summary.strip())
    ):
        project.summary = data["summary"][:2048]
    if "image_url" in data and data["image_url"] and (not project.image_url):
        project.image_url = data["image_url"][:2048]
    if "source_url" in data and data["source_url"] and (not project.source_url):
        project.source_url = data["source_url"][:2048]
    if "webpage_url" in data and data["webpage_url"] and (not project.webpage_url):
        project.webpage_url = data["webpage_url"][:2048]
    if "contact_url" in data and data["contact_url"] and (not project.contact_url):
        project.contact_url = data["contact_url"][:2048]
    if "download_url" in data and data["download_url"] and (not project.download_url):
        project.download_url = data["download_url"][:2048]
    if "is_webembed" in data and data["is_webembed"]:
        project.is_webembed = True
    # Save the project state
    project.save()
    # Additional logs, if available
    if "commits" in data:
        SyncCommitData(project, data["commits"])


def AddProjectDataFromAutotext(project):
    """Fills the project from the configured remote URL."""
    try:
        data = GetProjectData(project.autotext_url, True)
        TrimProjectData(project, data)
    except ConnectionError as ex:
        flash("Data could not be synced.", "error")


def IsProjectStarred(project, current_user):
    """Check if a project has been starred by the current user."""
    if not isUserActive(current_user):
        return False
    return bool(
        Activity.query.filter_by(
            name="star", project_id=project.id, user_id=current_user.id
        ).one_or_none()
    )


def GetProjectACLs(user, event, starred):
    """Figure out some basic permissions."""
    lock_editing = event.lock_editing
    allow_post = starred and not event.lock_resources and event.has_started
    allow_edit = not user.is_anonymous and \
                 (user.is_admin or event.lock_resources)
    allow_edit = (starred or allow_edit) and not lock_editing
    return allow_edit, allow_post, lock_editing


def AllowProjectEdit(project, current_user):
    """Check if the project is editable by the user."""
    if not current_user or current_user.is_anonymous or not isUserActive(current_user):
        return False
    if not project or project.is_hidden:
        # Hidden projects are not editable
        return False
    if project.user_id == current_user.id:
        # The project owner can always edit
        return True
    if project.event.lock_resources:
        # In a Resource area, everyone can edit
        return True
    if project.event.user_id == current_user.id:
        # The event owner can always edit
        return True
    if current_user.is_admin:
        # Admins rule the world
        return True
    # Must be a member of the team in good standing
    return IsProjectStarred(project, current_user)


def AllowUserInEvent(user, event):
    """Check user permission to post in this event."""
    is_anonymous = not user or user.is_anonymous
    if not is_anonymous and not isUserActive(user):
        flash("Your account needs to be activated before you can post.", "warning")
        return redirect(url_for("public.event", event_id=event_id))
    if event.lock_starting or (event.has_finished and not user.is_admin):
        flash("Projects may no longer be started in this event.", "error")
        return redirect(url_for("public.event", event_id=event.id))
    if is_anonymous:
        flash("Your project will be private until it is approved.", "info")
    return True


def ProjectsByProgress(progress=None, event=None):
    """Fetch all projects by progress level."""
    if event is not None:
        projects = event.projects_for_event()
    else:
        return None
    if progress is not None:
        projects = projects.filter_by(progress=progress)
    projects = projects.filter_by(is_hidden=False)
    return projects.order_by(Project.category_id).all()


def GetEventUsers(event):
    """Fetch all active users that have a project in this event."""
    if not event or not event.projects:
        return []
    users = []
    userlist = []
    projects = set([p.id for p in event.projects])
    # TODO: slow; how about actual membership?
    activities = Activity.query.filter(
        and_(Activity.name == "star", Activity.project_id.in_(projects))
    ).all()
    for a in activities:
        if a.user and a.user.active and a.user_id not in userlist:
            userlist.append(a.user_id)
            users.append(a.user)
    return sorted(users, key=lambda x: x.username)


def ProjectActivity(project, of_type, user, action=None, comments=None):
    """Generate an activity of a certain type in the project."""
    activity = Activity(
        name=of_type,
        user_id=user.id,
        project_id=project.id,
        project_progress=project.progress,
        project_version=project.versions.count() - 1,
        action=action,
    )
    # Post comments are activity contents
    if comments is not None and len(comments) > 3:
        activity.content = comments
    # Check for existing stars
    if "star" in of_type:
        allstars = Activity.query.filter_by(
            name="star", project_id=project.id, user_id=user.id
        )
        if of_type == "star":
            # One star per user
            if allstars.count() > 0:
                return False
        elif of_type == "unstar":
            # Not an actual activity
            if allstars.count() > 0:
                allstars.first().delete()
                return True
            return False
    activity.project_score = project.score
    activity.save()
    # In case of an image, update the post
    if of_type == "update" and activity.content and "![" in activity.content:
        project.set_auto_image()
    return True


def CheckPrevCommits(commit, username, since, until, prevlinks, prevdates):
    # Check duplicates
    if "url" in commit and commit["url"] is not None:
        if commit["url"] in prevlinks:
            return None
    if commit["date"].replace(microsecond=0) in prevdates:
        return None
    if commit["date"] < since or commit["date"] > until:
        return None
    # Get message and author
    message = commit["message"]
    if username != commit["author"]:
        username = commit["author"]
        user = User.query.filter_by(username=username).first()
        if user is None:
            message += " (@%s)" % username or "git"
    return message


def SyncCommitData(project, commits):
    """Collect data for syncing a project from a remote site."""
    if project.event is None or len(commits) == 0:
        return
    prevactivities = Activity.query.filter_by(
        name="update", action="commit", project_id=project.id
    ).all()
    prevdates = [a.timestamp.replace(microsecond=0) for a in prevactivities]
    prevlinks = [a.ref_url for a in prevactivities]
    username = None
    user = None
    since = project.event.starts_at_tz
    until = project.event.ends_at_tz
    for commit in commits:
        message = CheckPrevCommits(commit, username, since, until, prevlinks, prevdates)
        if message is None:
            continue
        # Create object
        activity = Activity(
            name="update",
            action="commit",
            project_id=project.id,
            timestamp=commit["date"],
            content=message,
        )
        if "url" in commit and commit["url"] is not None:
            activity.ref_url = commit["url"]
        if user is not None:
            activity.user_id = user.id
        activity.save()
