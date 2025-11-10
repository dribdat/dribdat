# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.api.parser import GetProjectData
from dribdat.api.parser import get_huggingface_project
from dribdat.apifetch import FetchHuggingFaceProject
from requests.exceptions import ReadTimeout
import warnings


class TestRepoOther:
    """Fetch data from other Git repositories."""

    def test_codeberg(self, user, testapp):
        """Test parsing a Codeberg readme."""
        test_url = "https://codeberg.org/dribdat/dribdat"
        try:
            test_obj = GetProjectData(test_url, True)
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
            test_obj = GetProjectData(test_url, True)
        except ReadTimeout:
            return warnings.warn("GitLab is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "GitLab"
        assert "commits" in test_obj
        assert len(test_obj["commits"]) > 5

    def test_bitbucket(self, user, testapp):
        """Test parsing a Bitbucket readme (via Git)."""
        test_url = "https://bitbucket.org/dribdat/dribdat.git"
        try:
            test_obj = GetProjectData(test_url, True)
        except ReadTimeout:
            return warnings.warn("Bitbucket is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "Git"
        # TODO: support for commits
        #assert "commits" in test_obj
        #assert len(test_obj["commits"]) > 5
        #assert test_obj["commits"][-1]["message"] == "Initial cookiecutter-flask project"
        #assert len(data["commits"]) > 0
