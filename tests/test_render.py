# -*- coding: utf-8 -*-
"""Dribdat data rendering tests."""

from dribdat.boxout.datapackage import box_datapackage
from dribdat.boxout.ckan import box_dataset

class TestRender:
    """Here be render tests."""

    def test_datapackage(self, testapp):
        """Render a remote data package."""
        test_url = '📦 Data: [datapackage.json](https://meta.dribdat.cc/api/event/2/datapackage.json)'  # noqa: E501
        dpkg_html = box_datapackage(test_url)
        assert dpkg_html is not None
        assert "boxout" in dpkg_html
        assert "Awesome hackathon" in dpkg_html

    def test_ckan(self, testapp):
        """Render a dataset from CKAN."""
        test_url = 'https://opendata.swiss/de/dataset/21st-century-swiss-video-games'  # noqa: E501
        dpkg_html = box_dataset(test_url)
        assert dpkg_html is not None
        assert "boxout" in dpkg_html
