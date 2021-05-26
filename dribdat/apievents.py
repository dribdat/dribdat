# -*- coding: utf-8 -*-
""" Collecting events from remote repositories """

import logging
import requests
import datetime as dt
from dateutil import parser

def FetchGithubCommits(full_name, since=None, until=None):
    apiurl = "https://api.github.com/repos/%s/commits?per_page=50" % full_name
    if since is not None:
        apiurl += "&since=%s" % since.replace(microsecond=0).isoformat()
    if until is not None:
        apiurl += "&until=%s" % until.replace(microsecond=0).isoformat()
    data = requests.get(apiurl)
    if data.status_code != 200:
        print(data)
        logging.warn("Could not sync GitHub commits on %s" % full_name)
        return []
    json = data.json()
    if 'message' in json:
        logging.warn("Could not sync GitHub commits on %s: %s" % (full_name, json['message']))
        return []
    commitlog = []
    for entry in json:
        if not 'commit' in entry: continue
        commit = entry['commit']
        datestamp = parser.parse(commit['committer']['date'])
        if 'author' in entry and entry['author'] is not None and 'login' in entry['author']:
            author = entry['author']['login']
        else:
            author = commit['committer']['name'][:100]
        url = "https://github.com/%s" % full_name
        if 'html_url' in entry:
            url = entry['html_url']
        commitlog.append({
            'url': url,
            'date': datestamp,
            'author': author,
            'message': commit['message'][:256],
        })
    return commitlog
