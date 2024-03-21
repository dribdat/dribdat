# -*- coding: utf-8 -*-
"""Dribdat data rendering tests."""

from dribdat.boxout.datapackage import box_datapackage
from dribdat.boxout.ckan import box_dataset
from dribdat.onebox import format_webembed
from dribdat.apipackage import (
    event_to_data_package,
    load_file_datapackage,
    fetch_datapackage
)
from .factories import UserFactory, EventFactory, ProjectFactory
import pytest


@pytest.mark.usefixtures('db')
class TestRender:
    """Here be render tests."""

    TEST_DPKG = 'https://hack.opendata.ch/api/event/1/datapackage.json'
    TEST_CKAN = 'https://opendata.swiss/de/dataset/21st-century-swiss-video-games'
    FILE_MOCK = 'tests/mock/datapackage.json'

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
        updates = load_file_datapackage(self.FILE_MOCK)
        assert updates != {}
        assert 'events' in updates
        assert len(updates['events']) == 1
        # Dry run will not load projects, since event needs to be created
        update_all = load_file_datapackage(self.FILE_MOCK, False, True)
        assert 'projects' in update_all
        assert len(update_all['projects']) == 1

    def test_fetchpackage(self, testapp):
        """Fetch a remote data package."""
        dpkg = fetch_datapackage(self.TEST_DPKG)
        assert dpkg is not None
        assert 'events' in dpkg
        evt0 = dpkg['events'][0]
        assert evt0['name'] == "Open Energy Data Hackdays"

    def test_datapackage(self, testapp):
        """Render a remote data package."""
        test_url = "📦 Data: [datapackage.json](%s)" % self.TEST_DPKG  # noqa: E501
        dpkg_html = box_datapackage(test_url)
        assert dpkg_html is not None
        assert "boxout" in dpkg_html
        assert "Open Energy Data Hackdays" in dpkg_html

    def test_ckan(self, testapp):
        """Render a dataset from CKAN."""
        dpkg_html = box_dataset(self.TEST_CKAN)
        assert dpkg_html is not None
        assert "boxout" in dpkg_html

    def test_webrender(self, testapp):
        """Link conversion for popular embedded links."""
        project = ProjectFactory()
        project.save()
        assert not format_webembed('')
        url = '<iframe src="blah"></iframe>'
        assert format_webembed(url) is url
        url = 'test.PDF'
        assert '/project/' in format_webembed(url, project.id)
        url = 'https://query.wikidata.org/#SELECT%20%3Fitem%20%3FitemLabel%0AWHERE%0A%7B%0A' \
            + '%20%20%3Fitem%20wdt%3AP31%20wd%3AQ46855.%0A%20%20SERVICE%20wikibase%3Alabel%' \
            + '20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%0A%7D'
        assert 'embed.html' in format_webembed(url)
        url  = 'https://youtu.be/xm3YgoEiEDc?t=32399'
        assert 'youtube' in format_webembed(url)
        assert '?start=' in format_webembed(url)
