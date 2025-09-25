# -*- coding: utf-8 -*-
"""Collect events from remote repositories."""
from .git import clone_repo, get_git_log
from flask import current_app

import shutil

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
        commit_url = url.replace(".git", "") + "/commit/" + commit['sha']
        commitlog.append({
            "url": commit_url,
            "date": commit['date'],
            "author": commit['author_name'],
            "message": commit['message'],
        })
    return commitlog
