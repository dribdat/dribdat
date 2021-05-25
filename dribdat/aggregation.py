# -*- coding: utf-8 -*-
"""Utilities for aggregating data
"""

from dribdat.user.models import Activity, Resource, User
from dribdat.user import isUserActive, projectProgressList
from dribdat.database import db
from dribdat.apifetch import * # TBR

def GetProjectData(url):
    data = None
    if url.find('//gitlab.com') > 0:
        apiurl = re.sub(r'https?://gitlab\.com/', '', url).strip('/')
        if apiurl == url: return {}
        return FetchGitlabProject(apiurl)

    elif url.find('//github.com') > 0:
        apiurl = re.sub(r'https?://github\.com/', '', url).strip('/')
        if apiurl.endswith('.git'): apiurl = apiurl[:-4]
        if apiurl == url: return {}
        return FetchGithubProject(apiurl)

    elif url.find('//bitbucket.org') > 0:
        apiurl = re.sub(r'https?://bitbucket\.org', '', url).strip('/')
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
            project.summary = data['summary'][:120]
    if 'homepage_url' in data and data['homepage_url'] and not project.webpage_url:
        project.webpage_url = data['homepage_url'][:2048]
    if 'contact_url' in data and data['contact_url'] and not project.contact_url:
        project.contact_url = data['contact_url'][:255]
    if 'source_url' in data and data['source_url'] and not project.source_url:
        project.source_url = data['source_url'][:255]
    if 'image_url' in data and data['image_url'] and not project.image_url:
        project.image_url = data['image_url'][:255]
    project.update()
    db.session.add(project)
    db.session.commit()
    # Additional logs, if available
    if 'commits' in data:
        SyncCommitData(project, data['commits'])

def SyncResourceData(resource):
    url = resource.source_url
    if url.find('/datapackage.json') > 0:
        dpdata = FetchDataProject(url)
        resource.sync_content = dpdata.description
        resource.download_url = dpdata.homepage_url
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

def SuggestionsByProgress(progress=None, event=None):
    """ Fetch all resources """
    if event is not None:
        resources = event.resources_for_event()
    else:
        resources = Resource.query
    if progress is not None:
        resources = resources.filter_by(progress_tip=progress)
    resources = resources.filter_by(is_visible=True)
    return resources.order_by(Resource.type_id).all()

def SuggestionsTreeForEvent(event=None):
    """ Collect resources by progress """
    allres = SuggestionsByProgress(None, event)
    steps = []
    shown = []
    for ix, p in enumerate(projectProgressList(True, False)):
        rrr = []
        for r in allres:
            if r.progress_tip is not None and r.progress_tip == p[0]:
                rrr.append(r)
                shown.append(r.id)
        steps.append({
            'index': ix + 1, 'name': p[1], 'resources': rrr
        })
    # show progress-less resources
    rr0 = []
    for r in allres:
        if r.progress_tip is None or not r.id in shown: rr0.append(r)
    if len(rr0) > 0:
        steps.append({
            'name': '/etc', 'index': -1, 'resources': rr0
        })
    return steps

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

def ProjectActivity(project, of_type, current_user, action=None, comments=None, resource=None):
    activity = Activity(
        name=of_type,
        project_id=project.id,
        user_id=current_user.id,
        action=action
    )
    score = 1
    if comments is not None and len(comments) > 3:
        activity.content=comments
    if resource is not None:
        score = 2 # Double score for adding resources
        activity.resource_id=resource
    if project.score is None: project.score = 0
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
    # Booster stars to give projects special awards
    #if of_type == 'star' and current_user.is_admin:
    #    score = 10
    project.score = project.score + score
    activity.project_score = project.score
    project.save()
    db.session.add(activity)
    db.session.commit()


def SyncCommitData(project, commits):
    if project.event is None or project.user is None or len(commits)==0: return
    alldates = [ a.timestamp for a in Activity.query.filter_by(
        name='update', action='commit',
        project_id=project.id
    ).all() ]
    username = None
    user = None
    since = project.event.starts_at_tz
    until = project.event.ends_at_tz
    for commit in commits:
        if commit['date'] in alldates: continue
        if commit['date'] < since or commit['date'] > until: continue
        if username != commit['author']:
            username = commit['author']
            user = User.query.filter_by(username=username).first()
            if user is None: user = project.user
        message = commit['message']
        if 'url' in commit and commit['url'] is not None:
            if 'github.com' in commit['url']:
                message += ' ([GitHub](%s))' % commit['url']
        activity = Activity(
            name='update', action='commit',
            project_id=project.id, user_id=user.id,
            timestamp=commit['date'],
            content=message
        )
        db.session.add(activity)
    db.session.commit()
