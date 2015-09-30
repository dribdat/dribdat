# -*- coding: utf-8 -*-
"""Utilities for collecting data from third party sites
"""
import re
import requests
from base64 import b64decode

def GetProjectData(url):
    data = None
    if url.find('//github.com') > 0:
        apiurl = re.sub(r'https?://github\.com', 'https://api.github.com/repos', url)
        if apiurl == url: return {}
        data = requests.get(apiurl)
        if data.text.find('{') < 0: return {}
        json = data.json()
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
