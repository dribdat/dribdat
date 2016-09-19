# -*- coding: utf-8 -*-
"""Utilities for collecting data from third party sites
"""
import re
import requests
from base64 import b64decode
from pyquery import PyQuery as pq

from dribdat.user.models import Activity
from dribdat.database import db

def GetProjectData(url):
    data = None
    if url.find('//github.com') > 0:
        apiurl = re.sub(r'https?://github\.com', 'https://api.github.com/repos', url)
        if apiurl == url: return {}
        data = requests.get(apiurl)
        if data.text.find('{') < 0: return {}
        json = data.json()
        if not 'name' in json: return {}
        readmeurl = "%s/readme" % apiurl
        readmedata = requests.get(readmeurl)
        if readmedata.text.find('{') < 0: return {}
        readme = readmedata.json()
        return {
            'name': json['name'],
            'summary': json['description'],
            'description': b64decode(readme['content']),
            'homepage_url': json['homepage'],
            'source_url': json['html_url'],
            'image_url': json['owner']['avatar_url'],
        }
    elif url.find('//make.opendata.ch/wiki') > 0:
        data = requests.get(url)
        if data.text.find('<div class="dw-content">') < 0: return {}
        doc = pq(data.text)
        content = doc("div.dw-content")
        if len(content) < 1: return {}
        ptitle = doc("p.pageId span")
        if len(ptitle) < 1: return {}
        return {
            'name': ptitle.text().replace('project:', ''),
            # 'summary': json['description'],
            'description': content.html(),
            # 'homepage_url': url,
            # 'source_url': json['html_url'],
            # 'image_url': json['owner']['avatar_url'],
        }
    return {}

def GetProjectScore(project):
    score = 0
    cqu = Activity.query.filter_by(project_id=project.id)
    c_s = cqu.filter_by(name="star").count()
    score = score + (2 * c_s)
    c_a = cqu.filter_by(name="boost").count()
    score = score + (10 * c_a)
    if len(project.summary) > 3: score = score + 3
    if len(project.image_url) > 3: score = score + 3
    if len(project.source_url) > 3: score = score + 10
    if len(project.webpage_url) > 3: score = score + 10
    if len(project.logo_color) > 3: score = score + 1
    if len(project.logo_icon) > 3: score = score + 1
    if len(project.longtext) > 3: score = score + 1
    if len(project.longtext) > 100: score = score + 4
    if len(project.longtext) > 500: score = score + 10
    return score

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
        if current_user.is_admin:
            score = 10
        project.score = project.score - score
        project.save()
        return
    # Admin stars give projects special awards
    if of_type == 'star' and current_user.is_admin:
        score = 10
    project.score = project.score + score
    project.save()
    db.session.add(activity)
    db.session.commit()
