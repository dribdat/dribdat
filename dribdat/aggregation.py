# -*- coding: utf-8 -*-
"""Utilities for aggregating data
"""

from dribdat.user.models import Activity, User
from dribdat.user import isUserActive, projectProgressList
from dribdat.database import db
from dribdat.apifetch import * # TBR

import json

def GetProjectData(url):
    data = None
    if url.find('//gitlab.com') > 0:
        apiurl = url
        apiurl = re.sub(r'(?i)-?/blob/[a-z]+/README.*', '', apiurl)
        apiurl = re.sub(r'https?://gitlab\.com/', '', apiurl).strip('/')
        if apiurl == url: return {}
        return FetchGitlabProject(apiurl)

    elif url.find('//github.com') > 0:
        apiurl = url
        apiurl = re.sub(r'(?i)/blob/[a-z]+/README.*', '', apiurl)
        apiurl = re.sub(r'https?://github\.com/', '', apiurl).strip('/')
        if apiurl.endswith('.git'): apiurl = apiurl[:-4]
        if apiurl == url: return {}
        return FetchGithubProject(apiurl)

    elif url.find('//bitbucket.org') > 0:
        apiurl = url
        apiurl = re.sub(r'(?i)/src/[a-z]+/(README)?\.?[a-z]*', '', apiurl)
        apiurl = re.sub(r'https?://bitbucket\.org', '', apiurl).strip('/')
        if apiurl == url: return {}
        return FetchBitbucketProject(apiurl)

    # The fun begins
    elif url.find('/datapackage.json') > 0:
        return FetchDataProject(url)

    # Now we're really rock'n'rollin'
    else:
        return FetchWebProject(url)

def SyncProjectData(project, data):
    # Project name should *not* be updated
    # Always update "autotext" field
    if 'description' in data and data['description']:
        project.autotext = data['description']
    # Update following fields only if blank
    if 'summary' in data and data['summary']:
        if not project.summary or not project.summary.strip():
            project.summary = data['summary'][:140]
    if 'homepage_url' in data and data['homepage_url'] and not project.webpage_url:
        project.webpage_url = data['homepage_url'][:2048]
    if 'contact_url' in data and data['contact_url'] and not project.contact_url:
        project.contact_url = data['contact_url'][:2048]
    if 'source_url' in data and data['source_url'] and not project.source_url:
        project.source_url = data['source_url'][:2048]
    if 'download_url' in data and data['download_url'] and not project.download_url:
        project.download_url = data['download_url'][:2048]
    if 'image_url' in data and data['image_url'] and not project.image_url:
        project.image_url = data['image_url'][:2048]
    project.update()
    db.session.add(project)
    db.session.commit()
    # Additional logs, if available
    if 'commits' in data:
        SyncCommitData(project, data['commits'])

# The above, in one step
def SyncResourceData(resource):
    url = resource.source_url
    dpdata = GetProjectData(url)
    resource.sync_content = json.dumps(dpdata)
    db.session.add(resource)
    db.session.commit()

def IsProjectStarred(project, current_user):
    if not isUserActive(current_user):
        return False
    return Activity.query.filter_by(
        name='star',
        project_id=project.id,
        user_id=current_user.id
    ).count() > 0

def ProjectsByProgress(progress=None, event=None):
    """ Fetch all projects by progress level """
    if event is not None:
        projects = event.projects_for_event()
    else:
        return None
    if progress is not None:
        projects = projects.filter_by(progress=progress)
    projects = projects.filter_by(is_hidden=False)
    return projects.order_by(Project.category_id).all()

def GetEventUsers(event):
    if not event.projects: return None
    users = []
    userlist = []
    for p in event.projects:
        for u in p.team():
            if u.active and not u.id in userlist:
                userlist.append(u.id)
                users.append(u)
    return sorted(users, key=lambda x: x.username)

def ProjectActivity(project, of_type, current_user, action=None, comments=None):
    activity = Activity(
        name=of_type,
        project_id=project.id,
        action=action
    )
    activity.user_id = current_user.id
    # Regular posts are 1 star
    score = 1
    # Booster stars to give projects special awards
    if of_type == 'boost': score = 10
    # Post comments are activity contents
    if comments is not None and len(comments) > 3:
        activity.content=comments
    if project.score is None: project.score = 0
    # Check for existing stars
    allstars = Activity.query.filter_by(
        name='star',
        project_id=project.id,
        user_id=current_user.id
    )
    if of_type == 'star':
        if allstars.count() > 0:
            return # One star per user
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


def SyncCommitData(project, commits):
    if project.event is None or project.user is None or len(commits)==0: return
    prevactivities = Activity.query.filter_by(
            name='update', action='commit', project_id=project.id
        ).all()
    prevdates = [ a.timestamp.replace(microsecond=0) for a in prevactivities ]
    prevlinks = [ a.ref_url for a in prevactivities ]
    username = None
    user = None
    since = project.event.starts_at_tz
    until = project.event.ends_at_tz
    for commit in commits:
        # Check duplicates
        if 'url' in commit and commit['url'] is not None:
            if commit['url'] in prevlinks: continue
        if commit['date'].replace(microsecond=0) in prevdates: continue
        if commit['date'] < since or commit['date'] > until: continue
        # Get message and author
        message = commit['message']
        if username != commit['author']:
            username = commit['author']
            user = User.query.filter_by(username=username).first()
            if user is None:
                message += ' (@%s)' % username or "git"
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
