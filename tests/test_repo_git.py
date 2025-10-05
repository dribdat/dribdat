# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.git import clone_repo, get_git_log, get_file_content
import os
import shutil
import subprocess

class TestGit:
    """Test the git library."""

    def test_get_git_log(self):
        """Test getting the git log."""
        path = clone_repo("https://github.com/dribdat/dridbot.git")
        log = get_git_log(path)
        print(len(log), leg[0]['message'])
        assert len(log) > 5
        assert log[0]['message'] == 'Initial commit'
        content = get_file_content(path, "README.md")
        assert "Dridbot" in content

