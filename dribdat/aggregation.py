# -*- coding: utf-8 -*-
"""Utilities for aggregating data."""

from dribdat.user.models import Activity, User, Project
from dribdat.user import isUserActive
from dribdat.database import db
from dribdat.apifetch import (
    FetchGitlabProject,
    FetchGithubProject,
    FetchGiteaProject,
    FetchBitbucketProject,
    FetchDataProject,
    FetchWebProject,
)
import json
import re
from sqlalchemy import and_


def GetProjectData(url):
    """Parse the Readme URL to collect remote data."""
    # TODO: find a better way to decide the kind of repo
    if url.find('//gitlab.com') > 0:
        return get_gitlab_project(url)

    elif url.find('//github.com') > 0:
        return get_github_project(url)

    elif url.find('//codeberg.org') > 0:
        # TODO: especially here..
        return get_gitea_project(url)

    elif url.find('//bitbucket.org') > 0:
        return get_bitbucket_project(url)

    # The fun begins
    elif url.find('.json') > 0:  # not /datapackage
        return FetchDataProject(url)

    # Now we're really rock'n'rollin'
    else:
        return FetchWebProject(url)


def get_gitlab_project(url):
    apiurl = url
    apiurl = re.sub(r'(?i)-?/blob/[a-z]+/README.*', '', apiurl)
    apiurl = re.sub(r'https?://gitlab\.com/', '', apiurl).strip('/')
    if apiurl == url:
        return {}
    return FetchGitlabProject(apiurl)


def get_github_project(url):
    apiurl = url
    apiurl = re.sub(r'(?i)/blob/[a-z]+/README.*', '', apiurl)
    apiurl = re.sub(r'https?://github\.com/', '', apiurl).strip('/')
    if apiurl.endswith('.git'):
        apiurl = apiurl[:-4]
    if apiurl == url:
        return {}
    if apiurl.endswith('.md'):
        return FetchWebProject(url)
    return FetchGithubProject(apiurl)


def get_gitea_project(url):
    apiurl = url
    apiurl = re.sub(r'(?i)/src/branch/[a-z]+/README.*', '', apiurl)
    apiurl = re.sub(r'https?://codeberg\.org/', '', apiurl).strip('/')
    if apiurl.endswith('.git'):
        apiurl = apiurl[:-4]
    if apiurl == url:
        return {}
    return FetchGiteaProject(apiurl)


def get_bitbucket_project(url):
    apiurl = url
    apiurl = re.sub(r'(?i)/src/[a-z]+/(README)?\.?[a-z]*', '', apiurl)
    apiurl = re.sub(r'https?://bitbucket\.org', '', apiurl).strip('/')
    if apiurl == url:
        return {}
    return FetchBitbucketProject(apiurl)


def AddProjectData(project):
    """Map remote fields to project data."""
    data = GetProjectData(project.autotext_url)
    if 'name' not in data:
        return project
    if len(data['name']) > 0:
        project.name = data['name'][0:80]
    if 'summary' in data and len(data['summary']) > 0:
        project.summary = data['summary'][0:140]
    if 'description' in data and len(data['description']) > 0:
        project.longtext = data['description']
    if 'homepage_url' in data and len(data['homepage_url']) > 0:
        project.webpage_url = data['homepage_url'][0:2048]
    if 'source_url' in data and len(data['source_url']) > 0:
        project.source_url = data['source_url'][0:2048]
    if 'image_url' in data and len(data['image_url']) > 0:
        project.image_url = data['image_url'][0:2048]
    if 'logo_icon' in data and len(data['logo_icon']) > 0:
        project.logo_icon = data['logo_icon'][0:40]
    return project


def SyncProjectData(project, data):
    """Sync remote project data."""
    # Note: project name should *not* be updated
    # Always update "autotext" field
    if 'description' in data and data['description']:
        project.autotext = data['description']
    # Update following fields only if blank
    if 'summary' in data and data['summary'] and \
       (not project.summary or not project.summary.strip()):
        project.summary = data['summary'][:140]
    if 'source_url' in data and data['source_url'] and \
       (not project.source_url):
        project.source_url = data['source_url'][:2048]
        if not project.longtext:
            project.longtext = project.source_url
    if 'homepage_url' in data and data['homepage_url'] and \
       (not project.webpage_url):
        project.webpage_url = data['homepage_url'][:2048]
        if not project.longtext:
            project.longtext = project.webpage_url
    if 'contact_url' in data and data['contact_url'] and \
       (not project.contact_url):
        project.contact_url = data['contact_url'][:2048]
    if 'download_url' in data and data['download_url'] and \
       (not project.download_url):
        project.download_url = data['download_url'][:2048]
    if 'image_url' in data and data['image_url'] and \
       (not project.image_url):
        project.image_url = data['image_url'][:2048]
    if 'is_webembed' in data and data['is_webembed']:
        project.is_webembed = True
    project.update()
    db.session.add(project)
    db.session.commit()
    # Additional logs, if available
    if 'commits' in data:
        SyncCommitData(project, data['commits'])


# The above, in one step
def SyncResourceData(resource):
    """Collect data from a remote resource."""
    url = resource.source_url
    dpdata = GetProjectData(url)
    resource.sync_content = json.dumps(dpdata)
    db.session.add(resource)
    db.session.commit()


def IsProjectStarred(project, current_user):
    """Check if a project has been starred by the current user."""
    if not isUserActive(current_user):
        return False
    return Activity.query.filter_by(
        name='star',
        project_id=project.id,
        user_id=current_user.id
    ).first() is not None


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
    """Fetch all users that have a project in this event."""
    if not event.projects:
        return None
    users = []
    userlist = []
    projects = set([p.id for p in event.projects])
    activities = Activity.query.filter(and_(
            Activity.name=='star', 
            Activity.project_id.in_(projects)
        )).all()
    for a in activities:
        if a.user and a.user_id not in userlist:
            userlist.append(a.user_id)
            users.append(a.user)
    return sorted(users, key=lambda x: x.username)


def ProjectActivity(project, of_type, user, action=None, comments=None):
    """Generate an activity of a certain type in the project."""
    activity = Activity(
        name=of_type,
        project_id=project.id,
        project_progress=project.progress,
        project_version=project.versions.count(),
        action=action
    )
    activity.user_id = user.id
    # Regular posts are 1 star
    score = 1
    # Booster stars give projects double points
    if of_type == 'boost':
        score = 2
    # Post comments are activity contents
    if comments is not None and len(comments) > 3:
        activity.content = comments
    if project.score is None:
        project.score = 0
    # Check for existing stars
    allstars = Activity.query.filter_by(
        name='star',
        project_id=project.id,
        user_id=user.id
    )
    if of_type == 'star':
        if allstars.count() > 0:
            return  # One star per user
    elif of_type == 'unstar':
        if allstars.count() > 0:
            allstars[0].delete()
        project.score = project.score - score
        project.save()
        return
    # Save current project score
    project.score = project.score + score
    activity.project_score = project.score
    project.save()
    db.session.add(activity)
    db.session.commit()


def CheckPrevCommits(commit, username, since, until, prevlinks, prevdates):
    # Check duplicates
    if 'url' in commit and commit['url'] is not None:
        if commit['url'] in prevlinks:
            return None
    if commit['date'].replace(microsecond=0) in prevdates:
        return None
    if commit['date'] < since or commit['date'] > until:
        return None
    # Get message and author
    message = commit['message']
    if username != commit['author']:
        username = commit['author']
        user = User.query.filter_by(username=username).first()
        if user is None:
            message += ' (@%s)' % username or "git"
    return message


def SyncCommitData(project, commits):
    """Collect data for syncing a project from a remote site."""
    if project.event is None or len(commits) == 0:
        return
    prevactivities = Activity.query.filter_by(
            name='update', action='commit', project_id=project.id
        ).all()
    prevdates = [a.timestamp.replace(microsecond=0) for a in prevactivities]
    prevlinks = [a.ref_url for a in prevactivities]
    username = None
    user = None
    since = project.event.starts_at_tz
    until = project.event.ends_at_tz
    for commit in commits:
        message = CheckPrevCommits(
                        commit, username, since, until, prevlinks, prevdates)
        if message is None:
            continue
        # Create object
        activity = Activity(
            name='update', action='commit',
            project_id=project.id,
            timestamp=commit['date'],
            content=message
        )
        if 'url' in commit and commit['url'] is not None:
            activity.ref_url = commit['url']
        if user is not None:
            activity.user_id = user.id
        activity.save()
    db.session.commit()
