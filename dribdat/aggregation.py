# -*- coding: utf-8 -*-
"""Utilities for aggregating data
"""

from dribdat.user.models import Activity
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

def IsProjectStarred(project, current_user):
    return Activity.query.filter_by(
        name='star',
        project_id=project.id,
        user_id=current_user.id
    ).count() > 0

def GetProjectTeam(project):
    return Activity.query.filter_by(
        name='star',
        project_id=project.id
    ).all()

def ProjectActivity(project, of_type, current_user):
    activity = Activity(
        name=of_type,
        project_id=project.id,
        user_id=current_user.id
    )
    score = 0
    if project.score is None: project.score = 0
    allstars = Activity.query.filter_by(
        name='star',
        project_id=project.id,
        user_id=current_user.id
    )
    if of_type == 'star':
        score = 2
        if allstars.count() > 0:
            return # One star per user
    elif of_type == 'unstar':
        score = 2
        if allstars.count() > 0:
            allstars[0].delete()
        #if current_user.is_admin:
        #    score = 10
        project.score = project.score - score
        project.save()
        return
    # Admin stars give projects special awards
    #if of_type == 'star' and current_user.is_admin:
    #    score = 10
    project.score = project.score + score
    project.save()
    db.session.add(activity)
    db.session.commit()
