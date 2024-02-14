# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import GetProjectData
from requests.exceptions import ReadTimeout
import warnings

class TestRepository:
    """Here be dataragons."""

    def test_dribdat(self):
        """Test parsing a remote dribdat project."""
        test_url = 'https://meta.dribdat.cc/project/4'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("meta.dribdat.cc is not accessible")
        assert 'name' in test_obj
        assert test_obj['type'] == 'Dribdat'
        assert 'dribdat' in test_obj['description']
        assert 'dribdat/dribdat' in test_obj['source_url']

    def test_datapackage_dribdat(self):
        """Test parsing a dribdat Data Package."""
        test_url = 'https://raw.githubusercontent.com/dribdat/dribdat/main/tests/mock/datapackage.json'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        assert 'name' in test_obj
        assert test_obj['type'] == 'Data Package'
        assert 'dribdat' in test_obj['description']
        assert test_url == test_obj['source_url']

    def test_datapackage(self):
        """Test parsing a standard Data Package."""
        test_url = 'https://raw.githubusercontent.com/OpenEnergyData/energy-data-ch/master/datapackage.json'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        assert 'name' in test_obj
        assert test_obj['type'] == 'Data Package'
        assert 'Datasets' in test_obj['summary']
        assert test_url == test_obj['source_url']

    def test_gitea(self):
        """Test parsing a Codeberg readme."""
        test_url = 'https://codeberg.org/dribdat/dribdat'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("Codeberg is not accessible")
        assert 'name' in test_obj
        assert test_obj['name'] == 'dribdat'
        assert test_obj['type'] == 'Gitea'
        assert 'commits' in test_obj
        assert len(test_obj['commits']) > 5

    def test_github(self):
        """Test parsing a GitHub readme."""
        test_url = 'https://github.com/dribdat/dribdat/blob/main/README.md'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        assert 'name' in test_obj
        assert test_obj['name'] == 'dribdat'
        assert test_obj['type'] == 'GitHub'
        assert 'commits' in test_obj
        assert len(test_obj['commits']) > 5
        assert '(dribdat/static/img' not in test_obj['description']
        assert '(https://raw.githubusercontent.com/' in test_obj['description']

    def test_github_other(self):
        """Test parsing a GitHub Markdown file."""
        test_url = 'https://github.com/dribdat/docs/blob/main/docs/sync.md'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        print(test_obj)
        assert 'name' in test_obj
        assert test_obj['name'] == 'sync'
        assert test_obj['type'] == 'Markdown'
        assert len(test_obj['description']) > 50

    def test_github_gist(self):
        """Test parsing a GitHub Gist."""
        test_url = 'https://gist.github.com/loleg/ebe8c96be5a8ef2465e5c573216f13b5'
        try:
            test_gist = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub Gist is not accessible")
        assert 'name' in test_gist
        assert test_gist['name'] == 'Gist'
        assert test_gist['type'] == 'Markdown'
        assert 'description' in test_gist
        assert len(test_gist['description']) > 50

    def test_gitlab(self):
        """Test parsing a GitLab readme."""
        test_url = 'https://gitlab.com/seismist/dribdat'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitLab is not accessible")
        assert 'name' in test_obj
        assert test_obj['name'] == 'dribdat'
        assert test_obj['type'] == 'GitLab'
        assert 'commits' in test_obj
        assert len(test_obj['commits']) > 5

    def test_bitbucket(self):
        """Test parsing a Bitbucket readme."""
        test_url = 'https://bitbucket.org/dribdat/dribdat/src/master/'
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("Bitbucket is not accessible")
        assert 'name' in test_obj
        assert test_obj['name'] == 'dribdat'
        assert test_obj['type'] == 'Bitbucket'
        # TODO: support for commits
