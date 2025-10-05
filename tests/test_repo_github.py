# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import GetProjectData
from requests.exceptions import ReadTimeout
import warnings


class TestRepoHub:
    """Here be dataragons."""

    def test_github(self, user, testapp):
        """Test parsing a GitHub readme."""
        return warnings.warn("GitHub tests skipped")
        test_url = "https://github.com/dribdat/dribdat/blob/main/README.md"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "GitHub"
        assert "commits" in test_obj
        assert len(test_obj["commits"]) > 5
        assert "(dribdat/static/img" not in test_obj["description"]
        assert "https://raw.githubusercontent.com/" in test_obj["description"]

    def test_github_other(self, user, testapp):
        """Test parsing a GitHub Markdown file."""
        return warnings.warn("GitHub tests skipped")
        test_url = "https://github.com/dribdat/docs/blob/main/docs/sync.md"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        print(test_obj)
        assert "name" in test_obj
        assert test_obj["name"] == "sync"
        assert test_obj["type"] == "Markdown"
        assert len(test_obj["description"]) > 50

    def test_github_gist(self, user, testapp):
        """Test parsing a GitHub Gist."""
        return warnings.warn("GitHub tests skipped")
        test_url = "https://gist.github.com/loleg/ebe8c96be5a8ef2465e5c573216f13b5"
        try:
            test_gist = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub Gist is not accessible")
        assert "name" in test_gist
        assert test_gist["name"] == "Gist"
        assert test_gist["type"] == "Markdown"
        assert "description" in test_gist
        assert len(test_gist["description"]) > 50

    def test_github_issue(self, user, testapp):
        """Test parsing a GitHub Issue."""
        return warnings.warn("GitHub tests skipped")
        test_url = "https://github.com/dribdat/dribdat/issues/424"
        try:
            test_git = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub Issue is not accessible")
        assert "name" in test_git
        assert "Challenge" in test_git["name"]
        assert "description" in test_git
        assert len(test_git["description"]) > 50

