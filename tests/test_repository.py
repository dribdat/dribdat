# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import GetProjectData
from dribdat.git import clone_repo, get_git_log, get_file_content
from requests.exceptions import ReadTimeout
import warnings
import os
import shutil
import subprocess

class TestGit:
    """Test the git library."""

    def setup_method(self):
        """Create a temporary git repository."""
        self.path = "/tmp/test_repo"
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.makedirs(self.path)
        subprocess.check_call(['git', 'init'], cwd=self.path)
        subprocess.check_call(['git', 'config', 'user.name', 'Test User'], cwd=self.path)
        subprocess.check_call(['git', 'config', 'user.email', 'test@example.com'], cwd=self.path)
        with open(os.path.join(self.path, "README.md"), "w") as f:
            f.write("This is a test.")
        subprocess.check_call(['git', 'add', '.'], cwd=self.path)
        subprocess.check_call(['git', 'commit', '-m', 'Initial commit'], cwd=self.path)

    def teardown_method(self):
        """Remove the temporary repository."""
        if os.path.exists(self.path):
            shutil.rmtree(self.path)

    def test_clone_repo(self):
        """Test cloning a repository."""
        clone_path = clone_repo(self.path)
        assert os.path.exists(clone_path)
        assert os.path.exists(os.path.join(clone_path, "README.md"))
        shutil.rmtree(clone_path)

    def test_get_git_log(self):
        """Test getting the git log."""
        log = get_git_log(self.path)
        assert len(log) == 1
        assert log[0]['message'] == 'Initial commit'

    def test_get_file_content(self):
        """Test getting file content."""
        content = get_file_content(self.path, "README.md")
        assert content == "This is a test."


class TestRepository:
    """Here be dataragons."""

    def test_dribdat(self, user, testapp):
        """Test parsing a remote dribdat project."""
        test_url = "https://hack.opendata.ch/project/2"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("Remote dribdat (hackopendata) is not accessible")
        assert "name" in test_obj
        assert test_obj["type"] == "Dribdat"
        assert "electricity" in test_obj["description"]
        assert "metaodi/open" in test_obj["source_url"]

    def test_datapackage_dribdat(self, user, testapp):
        """Test parsing a dribdat Data Package."""
        test_url = "https://raw.githubusercontent.com/dribdat/dribdat/main/tests/mock/datapackage.json"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        assert "name" in test_obj
        assert test_obj["type"] == "Data Package"
        assert "dribdat" in test_obj["description"]
        assert test_url == test_obj["source_url"]

    def test_datapackage(self, user, testapp):
        """Test parsing a standard Data Package."""
        test_url = "https://raw.githubusercontent.com/OpenEnergyData/energy-data-ch/master/datapackage.json"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("GitHub is not accessible")
        assert "name" in test_obj
        assert test_obj["type"] == "Data Package"
        assert "Datasets" in test_obj["summary"]
        assert test_url == test_obj["source_url"]

    def test_gitea(self, user, testapp):
        """Test parsing a Codeberg readme."""
        test_url = "https://codeberg.org/dribdat/dribdat"
        try:
            test_obj = GetProjectData(test_url)
        except ReadTimeout:
            return warnings.warn("Codeberg is not accessible")
        assert "name" in test_obj
        assert test_obj["name"] == "dribdat"
        assert test_obj["type"] == "Gitea"
        assert "commits" in test_obj
        assert len(test_obj["commits"]) > 5

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
