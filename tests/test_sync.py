# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import (
    AddProjectDataFromAutotext,
    TrimProjectData, 
    FetchWebProject,
    ProjectActivity,
)
from .factories import ProjectFactory

import random
from string import ascii_uppercase

class TestSync:
    """Testing sync and aggregation features."""

    def test_data_mapping(self, user, testapp):
        """Test mapping from Data Package."""
        project = ProjectFactory()
        project.autotext_url = 'https://raw.githubusercontent.com/dribdat/dribdat/main/tests/mock/datapackage.json'
        project.save()
        # Fetch from project configuration
        AddProjectDataFromAutotext(project)
        assert 'Awesome' in project.summary
        # More thorough tests
        thedata = project.data
        a_long_random_string = random.choices(ascii_uppercase, k=5000)
        thedata['name'] = a_long_random_string
        thedata['summary'] = a_long_random_string
        thedata['webpage_url'] = a_long_random_string
        thedata['logo_icon'] = a_long_random_string
        TrimProjectData(project, thedata)
        assert len(project.name) == 80
        assert len(project.summary) == 140
        assert len(project.webpage_url) == 2048
        assert len(project.logo_icon) == 40


    def test_dokuwiki(self):
        """Test parsing a Dokuwiki."""
        test_url = 'https://make.opendata.ch/wiki/information:rules'
        test_obj = FetchWebProject(test_url)
        assert test_obj['type'] == 'DokuWiki'
        assert test_obj['source_url'] == test_url
        assert 'Guidelines' in test_obj['description']

    def test_googledoc(self):
        """Test parsing a Google Document."""
        # Handbook to Hackathons with Dribdat
        test_url = 'https://docs.google.com/document/d/e/2PACX-1vR5Gv5NA3pkls0FRufC0dg-blkOhSo1LMX58pSNtj0FhZq1ImmLw0cIwmla_hiZaxtP8tnzJQQgZg94/pub'
        test_obj = FetchWebProject(test_url)
        assert 'description' in test_obj
        assert 'Handbook' in test_obj['description']

