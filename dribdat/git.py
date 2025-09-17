import subprocess
import os
from flask import current_app
from datetime import datetime
import tempfile
import shutil

def clone_repo(url):
    """Clones a git repository to a temporary directory."""
    path = tempfile.mkdtemp()
    try:
        subprocess.check_call(['git', 'clone', url, path])
        return path
    except subprocess.CalledProcessError as e:
        current_app.logger.error("Could not clone repo: %s", e)
        return None

def get_git_log(path):
    """Gets the git log for a repository."""
    if not os.path.exists(path):
        return []
    try:
        log = subprocess.check_output(
            ['git', 'log', '--pretty=format:%H%n%an%n%ae%n%at%n%s'],
            cwd=path
        ).decode('utf-8')
        commits = []
        commit_data = log.strip().split('\n')
        for i in range(0, len(commit_data), 5):
            if i + 4 < len(commit_data):
                commits.append({
                    'sha': commit_data[i],
                    'author_name': commit_data[i+1],
                    'author_email': commit_data[i+2],
                    'date': datetime.fromtimestamp(int(commit_data[i+3])),
                    'message': commit_data[i+4],
                })
        return commits
    except subprocess.CalledProcessError as e:
        current_app.logger.error("Could not get git log: %s", e)
        return []

def get_file_content(path, filename):
    """Gets the content of a file in a repository."""
    filepath = os.path.join(path, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return f.read()
