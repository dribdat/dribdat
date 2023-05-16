# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import FetchWebProject


class TestSync:
    """Here be moar dataragons."""


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

