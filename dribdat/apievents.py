# -*- coding: utf-8 -*-
"""Collect events from remote repositories."""

from .git import clone_repo, get_git_log
from flask import current_app
from dateutil import parser
import shutil
import requests

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10


def fetch_commits(url):
    """Fetch commits from a git repository."""
    repo_path = clone_repo(url)
    if not repo_path:
        return []
    commits = get_git_log(repo_path)
    shutil.rmtree(repo_path)
    commitlog = []
    for commit in commits:
        # construct commit url from base url
        commit_url = url.replace(".git", "") + "/commit/" + commit["sha"]
        commitlog.append(
            {
                "url": commit_url,
                "date": commit["date"],
                "author": commit["author_name"],
                "message": commit["message"],
            }
        )
    return commitlog


def fetch_commits_codeberg(full_name, limit=10):
    """Parse data about codeberg commits."""
    apiurl = "https://codeberg.org/api/v1/repos/%s/commits?limit=%d" % (
        full_name,
        limit,
    )
    data = requests.get(apiurl, timeout=REQUEST_TIMEOUT)
    if data.status_code != 200:
        current_app.logger.warning("Could not sync codeberg commits on %s" % full_name)
        return []
    json = data.json()
    if "message" in json:
        current_app.logger.warning(
            "Could not sync codeberg commits on %s: %s" % (full_name, json["message"])
        )
        return []
    commitlog = []
    for entry in json:
        if "commit" not in entry:
            continue
        url = entry["html_url"]
        commit = entry["commit"]
        datestamp = parser.parse(entry["created"])
        author = ""
        if "committer" in commit and "name" in commit["committer"]:
            author = commit["committer"]["name"]
        elif "author" in entry and "name" in commit["author"]:
            author = commit["author"]["name"]
        commitlog.append(
            {
                "url": url,
                "date": datestamp,
                "author": author,
                "message": commit["message"][:256],
            }
        )
    return commitlog


def fetch_commits_github(full_name, since=None, until=None):
    """Parse data about GitHub commits."""
    apiurl = "https://api.github.com/repos/%s/commits?per_page=50" % full_name
    if since is not None:
        apiurl += "&since=%s" % since.replace(microsecond=0).isoformat()
    if until is not None:
        apiurl += "&until=%s" % until.replace(microsecond=0).isoformat()
    data = requests.get(apiurl, timeout=REQUEST_TIMEOUT)
    if data.status_code != 200:
        current_app.logger.warning("Could not sync GitHub commits on %s" % full_name)
        return []
    json = data.json()
    if "message" in json:
        current_app.logger.warning(
            "Could not sync GitHub commits on %s: %s" % (full_name, json["message"])
        )
        return []
    return parse_github_commits(json, full_name)


def parse_github_commits(json, full_name):
    """Standardize data from a GitHub commit log."""
    commitlog = []
    for entry in json:
        if "commit" not in entry:
            continue
        commit = entry["commit"]
        datestamp = parser.parse(commit["committer"]["date"])
        author = ""
        if (
            "author" in entry
            and entry["author"] is not None
            and "login" in entry["author"]
        ):
            author = entry["author"]["login"]
        elif "committer" in commit:
            author = commit["committer"]["name"][:100]
        url = "https://github.com/%s" % full_name
        if "html_url" in entry:
            url = entry["html_url"]
        commitlog.append(
            {
                "url": url,
                "date": datestamp,
                "author": author,
                "message": commit["message"][:256],
            }
        )
    return commitlog


def fetch_commits_gitlab(project_id: int, since=None, until=None):
    """Parse data about GitLab commits."""
    apiurl = "https://gitlab.com/api/v4/"
    apiurl = apiurl + "projects/%d/repository/commits?" % project_id
    current_app.logger.info("Fetching commits: %s" % apiurl)
    if since is not None:
        apiurl += "&since=%s" % since.replace(microsecond=0).isoformat()
    if until is not None:
        apiurl += "&until=%s" % until.replace(microsecond=0).isoformat()
    # Collect basic data
    data = requests.get(apiurl, timeout=REQUEST_TIMEOUT)
    if data.text.find("{") < 0:
        return []
    json = data.json()
    if "message" in json:
        current_app.logger.warning("Could not sync GitLab commits", json["message"])
        return []
    commitlog = []
    for commit in json:
        if "message" not in commit:
            continue
        datestamp = parser.parse(commit["created_at"])
        author = ""
        if "author_name" in commit and commit["author_name"] is not None:
            author = commit["author_name"]
        commitlog.append(
            {
                "url": commit["web_url"],
                "date": datestamp,
                "author": author,
                "message": commit["message"][:256],
            }
        )
    return commitlog
