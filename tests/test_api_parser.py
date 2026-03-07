# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from dribdat.api.parser import (
    GetProjectData,
    get_gitlab_project,
    get_github_project,
    get_codeberg_project,
    get_huggingface_project
)

class TestApiParser:

    @patch('dribdat.api.parser.FetchGitlabProject')
    def test_get_gitlab_project(self, mock_fetch):
        mock_fetch.return_value = {'name': 'gitlab_project'}
        url = "https://gitlab.com/user/project"
        result = get_gitlab_project(url, False)
        assert result == {'name': 'gitlab_project'}
        mock_fetch.assert_called_once_with('user/project', False)

        # Test with README path
        url_readme = "https://gitlab.com/user/project/-/blob/main/README.md"
        result = get_gitlab_project(url_readme, False)
        assert result == {'name': 'gitlab_project'}
        mock_fetch.assert_called_with('user/project', False)

        # Empty
        assert get_gitlab_project("https://gitlab.com/", False) == {}

    @patch('dribdat.api.parser.FetchGithubProject')
    @patch('dribdat.api.parser.FetchWebGitHubGist')
    @patch('dribdat.api.parser.FetchWebGitHub')
    @patch('dribdat.api.parser.FetchGithubIssue')
    def test_get_github_project(self, mock_issue, mock_web, mock_gist, mock_project):
        # Regular project
        mock_project.return_value = {'name': 'gh_project'}
        url = "https://github.com/user/project"
        assert get_github_project(url, False) == {'name': 'gh_project'}
        mock_project.assert_called_once_with('user/project', False)

        # Gist
        mock_gist.return_value = {'name': 'gist'}
        url_gist = "https://gist.github.com/user/gistid"
        assert get_github_project(url_gist, False) == {'name': 'gist'}
        mock_gist.assert_called_once_with(url_gist)

        # Markdown (not README)
        mock_web.return_value = {'name': 'web_gh'}
        url_md = "https://github.com/user/project/blob/main/docs/guide.md"
        assert get_github_project(url_md, False) == {'name': 'web_gh'}
        mock_web.assert_called_once_with(url_md)

        # Issue
        mock_issue.return_value = {'name': 'issue'}
        url_issue = "https://github.com/user/project/issues/123"
        assert get_github_project(url_issue, False) == {'name': 'issue'}
        mock_issue.assert_called_once_with('user/project', 123)

        # Empty
        assert get_github_project("https://github.com/", False) == {}

        # .git suffix
        mock_project.return_value = {'name': 'gh_project_git'}
        assert get_github_project("https://github.com/user/project.git", False) == {'name': 'gh_project_git'}

    @patch('dribdat.api.parser.FetchCodebergProject')
    def test_get_codeberg_project(self, mock_fetch):
        mock_fetch.return_value = {'name': 'cb_project'}
        url = "https://codeberg.org/user/project"
        assert get_codeberg_project(url, False) == {'name': 'cb_project'}
        mock_fetch.assert_called_once_with('user/project', False)

        # .git suffix
        assert get_codeberg_project("https://codeberg.org/user/project.git", False) == {'name': 'cb_project'}

        # Empty
        assert get_codeberg_project("https://codeberg.org/", False) == {}

    @patch('dribdat.api.parser.FetchHuggingFaceProject')
    def test_get_huggingface_project(self, mock_fetch):
        mock_fetch.return_value = {'name': 'hf_project'}
        url = "https://huggingface.co/user/project"
        assert get_huggingface_project(url, False) == {'name': 'hf_project'}
        mock_fetch.assert_called_once_with('user/project', False)

        # Empty
        assert get_huggingface_project("https://huggingface.co/", False) == {}

    @patch('dribdat.api.parser.get_gitlab_project')
    @patch('dribdat.api.parser.get_huggingface_project')
    @patch('dribdat.api.parser.get_github_project')
    @patch('dribdat.api.parser.get_codeberg_project')
    @patch('dribdat.api.parser.FetchGitProject')
    @patch('dribdat.api.parser.FetchDataProject')
    @patch('dribdat.api.parser.FetchDribdatProject')
    @patch('dribdat.api.parser.FetchWebProject')
    def test_get_project_data(self, mock_web, mock_dribdat, mock_data, mock_git, mock_cb, mock_gh, mock_hf, mock_gl):
        # GitLab
        GetProjectData("https://gitlab.com/u/p")
        mock_gl.assert_called_once()

        # HF
        GetProjectData("https://huggingface.co/u/p")
        mock_hf.assert_called_once()

        # GitHub
        GetProjectData("https://github.com/u/p")
        mock_gh.assert_called_once()

        # Codeberg
        GetProjectData("https://codeberg.org/u/p")
        mock_cb.assert_called_once()

        # .git
        GetProjectData("https://example.com/repo.git")
        mock_git.assert_called_once()

        # .json
        GetProjectData("https://example.com/data.json")
        mock_data.assert_called_once()

        # Dribdat project
        mock_dribdat.return_value = {'name': 'dribdat'}
        GetProjectData("https://dribdat.example.com/project/1")
        mock_dribdat.assert_called_once()

        # Generic web
        GetProjectData("https://example.com/page")
        mock_web.assert_called_once()
