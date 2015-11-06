# -*- coding: utf-8 -*-
"""Utilities for collecting data from third party sites
"""
import re
import requests
from base64 import b64decode

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
    return {}

def GetProjectScore(project):
    score = 0
    cqu = Activity.query.filter_by(project_id=project.id)
    c_s = cqu.filter_by(name="star").count()
    score = score + (2 * c_s)
    c_a = cqu.filter_by(name="award").count()
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

def ProjectActivity(project, of_type, current_user):
    activity = Activity(
        name=of_type,
        project_id=project.id,
        user_id=current_user.id
    )
    score = 0
    if of_type == 'star':
        score = 2
        if Activity.query.filter_by(
            name=of_type,
            project_id=project.id,
            user_id=current_user.id
        ).count() > 0:
            return # One star per user
    if of_type == 'award':
        score = 10
    activity.score = score + GetProjectScore(project)
    db.session.add(activity)
    db.session.commit()
