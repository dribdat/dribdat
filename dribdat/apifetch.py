# -*- coding: utf-8 -*-
"""Collecting data from third party API repositories
"""

from future.standard_library import install_aliases
install_aliases()
from urllib.parse import quote_plus

import re
import requests
from base64 import b64decode
from pyquery import PyQuery as pq

def FetchGitlabProject(project_url):
    WEB_BASE = "https://gitlab.com/%s"
    API_BASE = "https://gitlab.com/api/v4/projects/%s"
    url_q = quote_plus(project_url)
    data = requests.get(API_BASE % url_q)
    if data.text.find('{') < 0: return {}
    json = data.json()
    if not 'name' in json: return {}
    readmeurl = "%s/raw/master/README.md" % (WEB_BASE % project_url)
    readmedata = requests.get(readmeurl)
    readme = readmedata.text or ""
    return {
        'name': json['name'],
        'summary': json['description'],
        'description': readme,
        # 'homepage_url': "",
        'source_url': json['web_url'],
        'image_url': json['avatar_url'],
        'contact_url': json['web_url'] + '/issues',
    }

def FetchGithubProject(project_url):
    API_BASE = "https://api.github.com/repos/%s"
    data = requests.get(API_BASE % project_url)
    if data.text.find('{') < 0: return {}
    json = data.json()
    if not 'name' in json: return {}
    readmeurl = "%s/readme" % (API_BASE % project_url)
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

def FetchBitbucketProject(project_url):
    WEB_BASE = "https://bitbucket.org/%s"
    API_BASE = "https://api.bitbucket.org/2.0/repositories/%s"
    data = requests.get(API_BASE % project_url)
    if data.text.find('{') < 0: return {}
    json = data.json()
    if not 'name' in json: return {}
    web_url = WEB_BASE % project_url
    readmedata = requests.get(web_url)
    if readmedata.text.find('class="readme') < 0: return {}
    doc = pq(readmedata.text)
    content = doc("div.readme")
    if len(content) < 1: return {}
    contact_url = json['website'] or web_url
    if json['has_issues']: contact_url = "%s/issues" % web_url
    image_url = ''
    if 'project' in json and 'links' in json['project'] and 'avatar' in json['project']['links']:
        image_url = json['project']['links']['avatar']['href']
    elif 'links' in json and 'avatar' in json['links']:
        image_url = json['links']['avatar']['href']
    return {
        'name': json['name'],
        'summary': json['description'],
        'description': content.html().strip(),
        'homepage_url': json['website'],
        'source_url': web_url,
        'image_url': image_url,
        'contact_url': contact_url,
    }

def FetchDokuwikiProject(project_url):
    data = requests.get(project_url)
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
        'contact_url': project_url,
    }
