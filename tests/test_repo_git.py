# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.git import clone_repo, get_git_log, get_file_content


class TestGit:
    """Run tests on the basic git library."""

    def test_get_git_log(self):
        """Test getting the git log."""
        path = clone_repo("https://github.com/dribdat/dridbot.git")
        log = get_git_log(path)
        assert len(log) > 5
        assert log[-1]['message'] == 'Initial bot'
        content = get_file_content(path, "README.md")
        assert "dridbot" in content

