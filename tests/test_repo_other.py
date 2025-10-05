# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import GetProjectData
from requests.exceptions import ReadTimeout
import warnings


class TestRepoApi:
    """Here be dataragons."""

    def test_codeberg(self, user, testapp):
        """Test parsing a Codeberg readme."""
        test_url = "https://codeberg.org/dribdat/dribdat"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("Codeberg is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "Codeberg"
        assert "commits" in test_obj
        assert len(test_obj["commits"]) > 5

    def test_gitlab(self, user, testapp):
        """Test parsing a GitLab readme."""
        test_url = "https://gitlab.com/seismist/dribdat"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitLab is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "GitLab"
        assert "commits" in test_obj
        assert len(test_obj["commits"]) > 5

    def test_bitbucket(self, user, testapp):
        """Test parsing a Bitbucket readme."""
        test_url = "https://bitbucket.org/dribdat/dribdat/src/master/"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("Bitbucket is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "Bitbucket"
        # TODO: support for commits
