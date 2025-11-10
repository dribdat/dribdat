# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.api.parser import GetProjectData
from dribdat.api.parser import get_huggingface_project
from dribdat.apifetch import FetchHuggingFaceProject
from requests.exceptions import ReadTimeout
import warnings


class TestRepoHuggingFace:
    """Fetch data from Hugging Face repositories."""

    def test_get_huggingface_project(self, user, testapp):
        """Test getting a Hugging Face project."""
        url = "https://huggingface.co/dribdat/test-model"
        with testapp.app.app_context():
            data = get_huggingface_project(url, True)
        assert "name" in data
        assert data["name"] == "dribdat/test-model"
        assert "description" in data
        assert "sample" in data["description"]
        assert "commits" in data
        assert len(data["commits"]) > 0

    def test_get_huggingface_dataset(self, user, testapp):
        """Test getting a Hugging Face project."""
        return # TODO: not implemented
        url = "https://huggingface.co/datasets/dribdat/test-dataset"
        with testapp.app.app_context():
            data = get_huggingface_project(url, True)
        assert "name" in data
        assert data["name"] == "dribdat/test-dataset"
        assert "description" in data
        assert "sample" in data["description"]
        assert "commits" in data
        assert len(data["commits"]) > 0
