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
        if not 'content' in readme: return {}
        return {
            'name': json['name'],
            'summary': json['description'],
            'description': b64decode(readme['content']).decode('utf-8'),
            'homepage_url': json['homepage'],
            'source_url': json['html_url'],
            'image_url': json['owner']['avatar_url'],
            'contact_url': json['html_url'] + '/issues',
        }
    elif url.find('//bitbucket.org') > 0:
        apiurl = re.sub(r'https?://bitbucket\.org', 'https://api.bitbucket.org/2.0/repositories', url)
        if apiurl == url: return {}
        data = requests.get(apiurl)
        if data.text.find('{') < 0: return {}
        json = data.json()
        if not 'name' in json: return {}
        readmedata = requests.get(url)
        if readmedata.text.find('class="readme') < 0: return {}
        doc = pq(readmedata.text)
        content = doc("div.readme")
        if len(content) < 1: return {}
        contact_url = json['website'] or url
        if json['has_issues']: contact_url = url + '/issues'
        image_url = ''
        if 'project' in json and 'links' in json['project']:
            image_url = json['project']['links']['avatar']['href']
        return {
            'name': json['name'],
            'summary': json['description'],
            'description': content.html().strip(),
            'homepage_url': json['website'],
            'source_url': url,
            'image_url': image_url,
            'contact_url': contact_url,
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
            'description': content.html().strip(),
            # 'homepage_url': url,
            # 'source_url': json['html_url'],
            # 'image_url': json['owner']['avatar_url'],
            'contact_url': url,
        }
    return {}

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
