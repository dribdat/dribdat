# -*- coding: utf-8 -*-
"""Dribdat data aggregation tests."""

from dribdat.aggregation import GetProjectData
from requests.exceptions import ReadTimeout
import warnings
import os
import shutil
import subprocess


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

