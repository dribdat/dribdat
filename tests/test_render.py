# -*- coding: utf-8 -*-
"""Dribdat data rendering tests."""

from dribdat.boxout.datapackage import box_datapackage


class TestRender:
    """Here be render tests."""

    def test_datapackage(self, testapp):
        """Render a data package."""
        test_url = '📦 Airport Codes: [datapackage.json](https://bucketeer-e34189e0-4cb3-496d-a72e-2dcf17cab858.s3.amazonaws.com/cividi/1/KUDZR3KIL28EPKUXI77VVJ45/datapackage.json)'  # noqa: E501
        dpkg_html = box_datapackage(test_url)
        assert "boxout" in dpkg_html
        assert "Airport Codes" in dpkg_html
