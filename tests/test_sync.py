# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import (
    AddProjectDataFromAutotext,
    SyncProjectData,
    TrimProjectData,
    FetchWebProject,
)
from dribdat.utils import fix_relative_links
from .factories import ProjectFactory

from .mock.project_data import project_data

import random
from string import ascii_uppercase


class TestSync:
    """Testing sync and aggregation features."""

    a_long_random_string = "".join(random.choices(ascii_uppercase, k=5000))

    def test_data_sync(self, user, testapp):
        """Test sync from Data Package."""
        project = ProjectFactory()
        thedata = project_data
        for o in [
            "name",
            "summary",
            "image_url",
            "source_url",
            "webpage_url",
            "contact_url",
            "download_url",
        ]:
            thedata[o] = self.a_long_random_string
        SyncProjectData(project, thedata)
        # The data should not be overwritten, if it exists in the project
        assert len(project.name) < 20
        assert len(project.summary) == 19
        assert len(project.image_url) == 32
        assert len(project.webpage_url) == 24
        # These fields are new
        assert len(project.source_url) == 2048
        assert len(project.contact_url) == 2048
        assert len(project.download_url) == 2048

    def test_data_mapping(self, user, testapp):
        """Test mapping from Data Package."""
        project = ProjectFactory()
        project.autotext_url = "https://raw.githubusercontent.com/dribdat/dribdat/main/tests/mock/datapackage.json"
        project.save()
        # Fetch from project configuration
        AddProjectDataFromAutotext(project)
        assert "Awesome" in project.summary
        thedata = project.data
        for o in [
            "name",
            "ident",
            "summary",
            "hashtag",
            "image_url",
            "source_url",
            "webpage_url",
            "contact_url",
            "download_url",
            "logo_icon",
        ]:
            thedata[o] = self.a_long_random_string
        TrimProjectData(project, thedata)
        assert len(project.name) == 80
        assert len(project.ident) == 10
        assert len(project.hashtag) == 140
        assert len(project.summary) == 2048
        assert len(project.image_url) == 2048
        assert len(project.source_url) == 2048
        assert len(project.webpage_url) == 2048
        assert len(project.contact_url) == 2048
        assert len(project.download_url) == 2048
        assert len(project.logo_icon) == 40  # not part of Sync

    def test_dokuwiki(self, user, testapp):
        """Test parsing a Dokuwiki."""
        test_url = "https://make.opendata.ch/wiki/information:rules"
        test_obj = FetchWebProject(test_url)
        assert test_obj is not None
        assert test_obj["type"] == "DokuWiki"
        assert test_obj["source_url"] == test_url
        assert "Guidelines" in test_obj["description"]

    def test_googledoc(self, user, testapp):
        """Test parsing a Google Document."""
        # Handbook to Hackathons with Dribdat
        test_url = "https://docs.google.com/document/d/e/2PACX-1vR5Gv5NA3pkls0FRufC0dg-blkOhSo1LMX58pSNtj0FhZq1ImmLw0cIwmla_hiZaxtP8tnzJQQgZg94/pub"
        test_obj = FetchWebProject(test_url)
        assert "description" in test_obj
        assert "Handbook" in test_obj["description"]

    def test_fix_relative_links(self):
        imgroot = "https://raw.githubusercontent.com"
        repo_full_name = "dribdat/dribdat"
        default_branch = "main"
        readme = '![hello there](world.png) <img title="hello" src="again.jpg">'
        readme = fix_relative_links(readme, imgroot, repo_full_name, default_branch)
        assert imgroot in readme
        assert "(world.png)" not in readme
        assert '"again.jpg"' not in readme

    def test_pretalx(self, user, testapp):
        """Test parsing a Pretalx page."""
        test_url = "https://pretalx.com/democon/talk/8SELAF/"
        test_obj = FetchWebProject(test_url)
        assert test_obj["type"] == "Pretalx"
        assert test_obj["source_url"] == test_url
        assert "Open" in test_obj["name"]
        assert "Architect" in test_obj["summary"]
        assert "Yard" in test_obj["description"]
