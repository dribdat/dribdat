# -*- coding: utf-8 -*-
"""Dribdat data rendering tests."""

from dribdat.boxout.datapackage import box_datapackage
from dribdat.boxout.ckan import box_dataset
from dribdat.apipackage import (
    event_to_data_package,
    load_file_datapackage,
    fetch_datapackage
)
from .factories import UserFactory, EventFactory
import pytest


@pytest.mark.usefixtures('db')
class TestRender:
    """Here be render tests."""

    TEST_DPKG = 'https://meta.dribdat.cc/api/event/2/datapackage.json'
    TEST_CKAN = 'https://opendata.swiss/de/dataset/21st-century-swiss-video-games'

    def test_localpackage(self, testapp):
        """Create and render a data package."""
        event = EventFactory()
        event.name = 'Awesome local hackathon'
        event.is_current = True
        event.save()
        user = UserFactory(active=True)  # A registered user
        user.save()
        host_url = 'http://localhost'
        package = event_to_data_package(event, user, host_url)
        assert package is not None
        assert 'title' in package
        assert package['title'] == 'Awesome local hackathon'

    def test_loadpackage(self, testapp):
        """Load a data package from a file."""
        updates = load_file_datapackage('tests/mock/datapackage.json')
        assert updates != {}
        assert 'events' in updates
        assert len(updates['events']) == 1
        # Dry run will not load projects, since event needs to be created
        update_all = load_file_datapackage('tests/mock/datapackage.json', False, True)
        assert 'projects' in update_all
        assert len(update_all['projects']) == 1

    def test_fetchpackage(self, testapp):
        """Fetch a remote data package."""
        dpkg = fetch_datapackage(self.TEST_DPKG)
        assert dpkg is not None
        assert 'events' in dpkg
        evt0 = dpkg['events'][0]
        assert evt0['name'] == "Awesome hackathon"

    def test_datapackage(self, testapp):
        """Render a remote data package."""
        test_url = "📦 Data: [datapackage.json](%s)" % self.TEST_DPKG  # noqa: E501
        dpkg_html = box_datapackage(test_url)
        assert dpkg_html is not None
        assert "boxout" in dpkg_html
        assert "Awesome hackathon" in dpkg_html

    def test_ckan(self, testapp):
        """Render a dataset from CKAN."""
        dpkg_html = box_dataset(self.TEST_CKAN)
        assert dpkg_html is not None
        assert "boxout" in dpkg_html
