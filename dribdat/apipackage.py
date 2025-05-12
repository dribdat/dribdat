# -*- coding: utf-8 -*-
"""Importing event data from a package"""

import requests
import json
import csv
import tempfile
from os import path
from copy import deepcopy
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app
from frictionless import Package, Resource
from .user.models import Event, Project, Activity, Category, User, Role
from .utils import format_date
from .apiutils import (
    get_project_list,
    get_event_users,
    get_event_activities,
    get_event_categories,
)
from dribdat.futures import UTC

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10


def event_to_data_package(event, author=None, host_url="", full_content=False):
    """Create a Data Package from the data of an event."""
    # Define the author, if available
    contributors = []
    if author and not author.is_anonymous:
        contributors.append(
            {"title": author.name, "path": author.webpage_url or "", "role": "author"}
        )
    else:
        # Disallow anon access to full data
        full_content = False

    # Compose hashtags
    if event.hashtags:
        keywords = event.hashtags.replace("#", "").split(" ")
    else:
        keywords = (["dribdat", "hackathon", "co-creation"],)

    # Set up a data package object
    package = Package(
        name="event-%d" % event.id,
        title=event.name,
        description=event.summary or event.description,
        keywords=keywords,
        sources=[{"title": "dribdat", "path": host_url}],
        licenses=[
            {
                "name": "ODC-PDDL-1.0",
                "path": "http://opendatacommons.org/licenses/pddl/",
                "title": "Open Data Commons Public Domain Dedication & License 1.0",
            }
        ],
        contributors=contributors,
        homepage=event.webpage_url or "",
        created=format_date(datetime.now(UTC)),
        version="0.9.0",
    )

    # Generate resources

    # print("Generating in-memory JSON of event")
    package.add_resource(
        Resource(
            name="events",
            data=[event.get_full_data()],
        )
    )
    # print("Generating in-memory JSON of projects")
    package.add_resource(
        Resource(
            name="projects",
            data=get_project_list(event.id, host_url, True),
        )
    )
    if full_content:
        # print("Generating in-memory JSON of participants")
        package.add_resource(
            Resource(
                name="users",
                data=get_event_users(event, full_content),
            )
        )
        # print("Generating in-memory JSON of activities")
        package.add_resource(
            Resource(
                name="activities",
                data=get_event_activities(event.id, 500),
            )
        )
        # print("Generating in-memory JSON of categories")
        package.add_resource(
            Resource(
                name="categories",
                data=get_event_categories(event.id),
            )
        )
        # print("Adding supplementary README")
        package.add_resource(
            Resource(
                name="readme",
                path="PACKAGE.txt",
            )
        )

    return package


def import_events_data(data, dry_run=False):
    """Collect data of a list of events."""
    updates = []
    for evt in data:
        name = evt["name"]
        event = Event.query.filter_by(name=name).first()
        if not event:
            current_app.logger.info("Creating event: %s" % name)
            event = Event()
        else:
            current_app.logger.info("Updating event: %s" % name)
        event.set_from_data(evt)
        if not dry_run:
            event.save()
        updates.append(event.data)
    return updates


def import_categories_data(data, dry_run=False):
    """Collect data of a list of categories."""
    updates = []
    for ctg in data:
        name = ctg["name"]
        category = Category.query.filter_by(name=name).first()
        if not category:
            current_app.logger.info("Creating category: %s" % name)
            category = Category()
        else:
            current_app.logger.info("Updating category: %s" % name)
        category.set_from_data(ctg)
        if not dry_run:
            category.save()
        updates.append(category.data)
    return updates


def import_users_data(data, dry_run=False):
    """Collect data of a list of users."""
    updates = []
    for usr in data:
        name = usr["username"]
        if name is None or len(name) < 4:
            continue
        email = usr["email"] if "email" in usr else ""
        if (
            User.query.filter_by(username=name).first()
            or User.query.filter_by(email=email).first()
        ):
            # Do not update existing user data
            current_app.logger.info("Skipping user: %s" % name)
            continue
        current_app.logger.info("Creating user: %s" % name)
        user = User()
        user.set_from_data(usr)
        import_user_roles(user, usr["roles"], dry_run)
        if not dry_run:
            user.save()
        updates.append(user.data)
    return updates


def import_user_roles(user, new_roles, dry_run=False):
    """Collect data of a list of roles."""
    updates = []
    my_roles = [r.name for r in user.roles]
    for r in new_roles.split(","):
        if r in my_roles:
            continue
        # Check that role is a new one
        if not Role.name:
            continue
        role = Role.query.filter(Role.name.ilike(r)).first()
        if not role:
            role = Role(r)
            if dry_run:
                continue
            role.save()
        user.roles.append(role)
        updates.append(role.name)
    return updates


def import_project_data(data, dry_run=False, event=None):
    """Collect data of a list of projects."""
    updates = []
    for pjt in data:
        # Skip empty rows
        if "name" not in pjt:
            current_app.logger.warning("Skipping empty row")
            current_app.logger.debug(pjt)
            continue
        # Get project name and content
        name = pjt["name"]
        if "longtext" not in pjt and "excerpt" in pjt:
            current_app.logger.warning("Importing excerpt as longtext")
            pjt["longtext"] = pjt.pop("excerpt")
        # Search for event
        event_name = None
        if "event_name" in pjt:
            event_name = pjt["event_name"]
        if event_name and (not event or event.name != event_name):
            event = Event.query.filter_by(name=event_name).first()
        if not event:
            current_app.logger.warning(
                "Skip [%s], event not found: %s" % (name, event_name)
            )
            continue
        # Search for project
        project = Project.query.filter_by(name=name).first()
        if not project:
            current_app.logger.info("Creating project: %s" % name)
            project = Project()
        else:
            current_app.logger.info("Updating project: %s" % name)
        project.set_from_data(pjt)
        project.update_null_fields()
        project.event_id = event.id
        if not dry_run:
            project.save()
        updates.append(project.data)
    return updates


def import_activities(data, dry_run=False):
    """Collect data from unique activities."""
    updates = []
    proj = None
    pname = ""
    for act in data:
        aname = act["name"]
        tstamp = datetime.utcfromtimestamp(act["time"])
        activity = Activity.query.filter_by(name=aname, timestamp=tstamp).first()
        if activity:
            current_app.logger.info("Skipping activity: %s", tstamp)
            continue
        current_app.logger.info("Creating activity: %s", tstamp)
        if act["project_name"] != pname:
            pname = act["project_name"]
            # TODO: unreliable; rather use a map of project_id to new id
            proj = Project.query.filter_by(name=pname).first()
        if not proj:
            current_app.logger.warning("Error! Project not found: %s" % pname)
            continue
        activity = Activity(aname, proj.id)
        activity.set_from_data(act)
        if not dry_run:
            activity.save()
        updates.append(activity.data)
    return updates


def import_event_package(data, dry_run=False, all_data=False):
    """Import an event from a Data Package."""
    if "sources" not in data or data["sources"][0]["title"] != "dribdat":
        return {"errors": ["Invalid source"]}
    updates = {}
    # Import in stages
    for stg in [1, 2, 3]:
        for res in data["resources"]:
            # Import events
            if stg == 1 and res["name"] == "events":
                updates["events"] = import_events_data(res["data"], dry_run)
            # Import categories
            elif stg == 1 and res["name"] == "categories" and all_data:
                updates["categories"] = import_categories_data(res["data"], dry_run)
            # Import user accounts
            elif stg == 1 and res["name"] == "users" and all_data:
                updates["users"] = import_users_data(res["data"], dry_run)
            # Projects follow users
            if stg == 2 and res["name"] == "projects" and all_data:
                updates["projects"] = import_project_data(res["data"], dry_run)
            # Activities always last
            if stg == 3 and res["name"] == "activities" and all_data:
                updates["activities"] = import_activities(res["data"], dry_run)
    # Return summary object
    return updates


def fetch_datapackage(url, dry_run=False, all_data=False):
    """Get event data from a URL."""
    # For security, can only be used from CLI.
    # In the future, we can add a subscription setting on the server side.
    if not url.endswith("datapackage.json"):
        current_app.logger.error("Invalid URL: %s", url)
        return {}
    try:
        data = requests.get(url, timeout=REQUEST_TIMEOUT).json()
        return import_event_package(data, dry_run, all_data)
    except json.decoder.JSONDecodeError:
        return {"errors": ["Could not load package due to JSON error"]}
    except requests.exceptions.RequestException:
        current_app.logger.error("Could not connect to %s" % url)
        return {}


def import_datapackage(filedata, dry_run=True, all_data=False):
    """Save a temporary file and provide details."""
    ext = filedata.filename.split(".")[-1].lower()
    if ext not in ["json"]:
        return {"errors": ["Invalid format (allowed: JSON)"]}
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = path.join(tmpdir, secure_filename(filedata.filename))
        filedata.save(filepath)
        return load_file_datapackage(filepath, dry_run, all_data)


def load_file_datapackage(filepath, dry_run=True, all_data=False):
    """Get event data from a file."""
    try:
        with open(filepath, mode="rb") as file:
            data = json.load(file)
        return import_event_package(data, dry_run, all_data)
    except json.decoder.JSONDecodeError:
        return {"errors": ["Could not load package due to JSON error"]}


def import_projects_csv(filedata, event=None, dry_run=True):
    """Save a temporary CSV file and import project data to event."""
    ext = filedata.filename.split(".")[-1].lower()
    if ext not in ["csv"]:
        return {"errors": ["Invalid format (allowed: CSV)"]}
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = path.join(tmpdir, secure_filename(filedata.filename))
        filedata.save(filepath)
        with open(filepath, mode="r") as csvfile:
            csvreader = csv.DictReader(csvfile)
            projdata = [deepcopy(row) for row in csvreader]
            return {"projects": import_project_data(projdata, dry_run, event)}


def import_users_csv(filedata, dry_run=True):
    """Import the user database from a file."""
    raise Exception("Not implemented")
