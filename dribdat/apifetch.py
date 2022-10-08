# -*- coding: utf-8 -*-
"""Collecting data from third party API repositories."""

from .apievents import FetchGithubCommits
from flask import url_for
from pyquery import PyQuery as pq  # noqa: N813
from base64 import b64decode
from flask_misaka import markdown
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from urllib.parse import quote_plus
import re
import requests
import bleach
from future.standard_library import install_aliases
install_aliases()


def FetchGitlabProject(project_url):
    WEB_BASE = "https://gitlab.com/%s"
    API_BASE = "https://gitlab.com/api/v4/projects/%s"
    url_q = quote_plus(project_url)
    data = requests.get(API_BASE % url_q)
    if data.text.find('{') < 0:
        return {}
    json = data.json()
    if 'name' not in json:
        return {}
    readmeurl = "%s/raw/master/README.md" % (WEB_BASE % project_url)
    readmedata = requests.get(readmeurl)
    readme = readmedata.text or ""
    return {
        'type': 'GitLab',
        'name': json['name'],
        'summary': json['description'],
        'description': readme,
        # 'homepage_url': "",
        'source_url': json['web_url'],
        'image_url': json['avatar_url'],
        'contact_url': json['web_url'] + '/issues',
    }


def FetchGitlabAvatar(email):
    apiurl = "https://gitlab.com/api/v4/avatar?email=%s&size=80"
    data = requests.get(apiurl % email)
    if data.text.find('{') < 0:
        return None
    json = data.json()
    if 'avatar_url' not in json:
        return None
    return json['avatar_url']


def FetchGithubProject(project_url):
    API_BASE = "https://api.github.com/repos/%s"
    data = requests.get(API_BASE % project_url)
    if data.text.find('{') < 0:
        return {}
    json = data.json()
    if 'name' not in json or 'full_name' not in json:
        return {}
    repo_full_name = json['full_name']
    default_branch = json['default_branch'] or 'main'
    readmeurl = "%s/readme" % (API_BASE % project_url)
    readmedata = requests.get(readmeurl)
    if readmedata.text.find('{') < 0:
        return {}
    readme = readmedata.json()
    if 'content' not in readme:
        readme = ''
    else:
        readme = b64decode(readme['content']).decode('utf-8')
        # Fix relative links in text
        imgroot = "https://raw.githubusercontent.com"
        readme = re.sub(
            r"<img src=\"(?!http)",
            "<img src=\"%s/%s/%s/" % (imgroot, repo_full_name, default_branch),
            readme
        )
        readme = re.sub(
            r"\!\[(.*)\]\((?!http)",
            # TODO check why we are using \g escape here?
            r"![\g<1>](%s/%s/%s/" % (imgroot, repo_full_name, default_branch),
            readme
        )
    return {
        'type': 'GitHub',
        'name': json['name'],
        'summary': json['description'],
        'description': readme,
        'homepage_url': json['homepage'],
        'source_url': json['html_url'],
        'image_url': json['owner']['avatar_url'],
        'contact_url': json['html_url'] + '/issues',
        'download_url': json['html_url'] + '/releases',
        'commits': FetchGithubCommits(repo_full_name)
    }


def FetchBitbucketProject(project_url):
    WEB_BASE = "https://bitbucket.org/%s"
    API_BASE = "https://api.bitbucket.org/2.0/repositories/%s"
    data = requests.get(API_BASE % project_url)
    if data.text.find('{') < 0:
        print('No data at', project_url)
        return {}
    json = data.json()
    if 'name' not in json:
        print('Invalid format at', project_url)
        return {}
    readme = ''
    for docext in ['.md', '.rst', '.txt', '']:
        readmedata = requests.get(
            API_BASE % project_url + '/src/HEAD/README.md')
        if readmedata.text.find('{"type":"error"') != 0:
            readme = readmedata.text
            break
    web_url = WEB_BASE % project_url
    contact_url = json['website'] or web_url
    if json['has_issues']:
        contact_url = "%s/issues" % web_url
    image_url = ''
    if 'project' in json and \
            'links' in json['project'] \
            and 'avatar' in json['project']['links']:
        image_url = json['project']['links']['avatar']['href']
    elif 'links' in json and 'avatar' in json['links']:
        image_url = json['links']['avatar']['href']
    return {
        'type': 'Bitbucket',
        'name': json['name'],
        'summary': json['description'],
        'description': readme,
        'homepage_url': json['website'],
        'source_url': web_url,
        'image_url': image_url,
        'contact_url': contact_url,
    }


DP_VIEWER_URL = 'http://data.okfn.org/tools/view?url=%s'


def FetchDataProject(project_url):
    """ Tries to load a Data Package formatted JSON file """
    # TODO: use frictionlessdata library!
    data = requests.get(project_url)
    if data.text.find('{') < 0:
        return {}
    json = data.json()
    if 'name' not in json or 'title' not in json:
        return {}
    if 'homepage' in json:
        readme_url = json['homepage']
    else:
        readme_url = project_url.replace('datapackage.json', 'README.md')
    text_content = ""
    if readme_url.startswith('http') and readme_url != project_url:
        text_content = requests.get(readme_url).text
    if not text_content and 'description' in json:
        text_content = json['description']
    contact_url = ''
    if 'maintainers' in json and \
            len(json['maintainers']) > 0 and \
            'web' in json['maintainers'][0]:
        contact_url = json['maintainers'][0]['web']
    return {
        'type': 'Data Package',
        'name': json['name'],
        'summary': json['title'],
        'description': text_content,
        # 'homepage_url': DP_VIEWER_URL % project_url,
        'source_url': project_url,
        'image_url': url_for('static', filename='img/datapackage_icon.png',
                             _external=True),
        'contact_url': contact_url,
    }


# Basis: https://github.com/mozilla/bleach/blob/master/bleach/sanitizer.py#L16
ALLOWED_HTML_TAGS = ALLOWED_TAGS + [
    'img', 'font', 'center', 'sub', 'sup', 'pre',
    'h1', 'h2', 'h3', 'h4', 'h5',
    'p', 'u', 'b', 'em', 'i',
]
ALLOWED_HTML_ATTR = ALLOWED_ATTRIBUTES
ALLOWED_HTML_ATTR['h1'] = ['id']
ALLOWED_HTML_ATTR['h2'] = ['id']
ALLOWED_HTML_ATTR['h3'] = ['id']
ALLOWED_HTML_ATTR['h4'] = ['id']
ALLOWED_HTML_ATTR['h5'] = ['id']
ALLOWED_HTML_ATTR['a'] = ['href', 'title', 'class', 'name']
ALLOWED_HTML_ATTR['img'] = ['src', 'width', 'height', 'alt', 'class']
ALLOWED_HTML_ATTR['font'] = ['color']


def FetchWebProject(project_url):
    try:
        data = requests.get(project_url)
    except requests.exceptions.RequestException:
        print("Could not connect to %s" % project_url)
        return {}

    # Google Document
    if project_url.startswith('https://docs.google.com/document'):
        return FetchWebGoogleDoc(data.text, project_url)
    # CodiMD / HackMD
    elif data.text.find('<div id="doc" ') > 0:
        return FetchWebCodiMD(data.text, project_url)
    # DokuWiki
    elif data.text.find('<meta name="generator" content="DokuWiki"/>') > 0:
        return FetchWebDokuWiki(data.text, project_url)
    # Etherpad
    elif data.text.find('pad.importExport.exportetherpad') > 0:
        return FetchWebEtherpad(data.text, project_url)
    # Instructables
    elif project_url.startswith('https://www.instructables.com/'):
        return FetchWebInstructables(data.text, project_url)


def FetchWebGoogleDoc(text, url):
    doc = pq(text)
    doc("style").remove()
    ptitle = doc("div#title") or doc("div#header")
    if len(ptitle) < 1:
        return {}
    content = doc("div#contents")
    if len(content) < 1:
        return {}
    html_content = bleach.clean(content.html().strip(), strip=True,
                                tags=ALLOWED_HTML_TAGS,
                                attributes=ALLOWED_HTML_ATTR)
    obj = {}
    # {
    #     'type': 'Google', ...
    #     'name': name,
    #     'summary': summary,
    #     'description': html_content,
    #     'image_url': image_url
    #     'source_url': project_url,
    # }
    obj['type'] = 'Google Docs'
    obj['name'] = ptitle.text()
    obj['description'] = html_content
    obj['source_url'] = url
    obj['image_url'] = url_for(
        'static', filename='img/document_icon.png', _external=True)
    return obj


def FetchWebCodiMD(text, url):
    doc = pq(text)
    ptitle = doc("title")
    if len(ptitle) < 1:
        return {}
    content = doc("div#doc").html()
    if len(content) < 1:
        return {}
    obj = {}
    obj['type'] = 'Markdown'
    obj['name'] = ptitle.text()
    obj['description'] = markdown(content)
    obj['source_url'] = url
    obj['image_url'] = url_for(
        'static', filename='img/codimd.png', _external=True)
    return obj


def FetchWebDokuWiki(text, url):
    doc = pq(text)
    ptitle = doc("span.pageId")
    if len(ptitle) < 1:
        return {}
    content = doc("div.dw-content")
    if len(content) < 1:
        return {}
    html_content = bleach.clean(content.html().strip(), strip=True,
                                tags=ALLOWED_HTML_TAGS,
                                attributes=ALLOWED_HTML_ATTR)
    obj = {}
    obj['type'] = 'DokuWiki'
    obj['name'] = ptitle.text().replace('project:', '')
    obj['description'] = html_content
    obj['source_url'] = url
    obj['image_url'] = url_for(
        'static', filename='img/dokuwiki_icon.png', _external=True)
    return obj


def FetchWebEtherpad(text, url):
    ptitle = url.split('/')[-1]
    if len(ptitle) < 1:
        return {}
    text_content = requests.get("%s/export/txt" % url).text
    obj = {}
    obj['type'] = 'Etherpad'
    obj['name'] = ptitle.replace('_', ' ')
    obj['description'] = text_content
    obj['source_url'] = url
    obj['image_url'] = url_for(
        'static', filename='img/document_white.png', _external=True)
    return obj


def FetchWebInstructables(text, url):
    doc = pq(text)
    ptitle = doc(".header-title")
    if len(ptitle) < 1:
        return {}
    content = doc(".main-content")
    if len(content) < 1:
        return {}
    html_content = ""
    for step in content.find(".step"):
        step_title = pq(step).find('.step-title')
        if step_title is not None:
            html_content += '<h3>' + step_title.text() + '</h3>'
        # Grab photos
        for img in pq(step).find('noscript'):
            if '{{ file' not in pq(img).html():
                html_content += pq(img).html()
        # Iterate through body
        step_content = pq(step).find('.step-body')
        if step_content is None:
            continue
        for elem in pq(step_content).children():
            if elem.tag == 'pre':
                if elem.text is None:
                    continue
                html_content += '<pre>' + elem.text + '</pre>'
            else:
                p = pq(elem).html()
                if p is None:
                    continue
                p = bleach.clean(p.strip(), strip=True,
                                 tags=ALLOWED_HTML_TAGS,
                                 attributes=ALLOWED_HTML_ATTR)
                html_content += '<%s>%s</%s>' % (elem.tag, p, elem.tag)
    obj = {}
    obj['type'] = 'Instructables'
    obj['name'] = ptitle.text()
    obj['description'] = html_content
    obj['source_url'] = url
    obj['image_url'] = url_for(
        'static', filename='img/instructables.png', _external=True)
    return obj
