# -*- coding: utf-8 -*-
"""Functional tests using WebTest.

See: http://webtest.readthedocs.org/
"""

from flask import url_for

from .factories import UserFactory, ProjectFactory, EventFactory
from dribdat.mailer import user_activation


class TestPosting:
    """Test posting activities (a.k.a. Dribs)."""

    def test_basic_posting(self, user, testapp):
        """Create a project and add some dribs."""

        # Make an admin user, project, and event
        admin = UserFactory(is_admin=True)
        admin.save()
        event = EventFactory()
        event.user = user
        event.save()
        project = ProjectFactory()
        project.user = admin
        project.event = event
        project.save()

        # Login the user
        my_hash = user_activation(admin)
        res = testapp.get(
            url_for("auth.activate", userid=admin.id, userhash=my_hash)
        ).follow()
        assert res.status_code == 200

        # Approve the project
        res = testapp.get(url_for("project.project_approve", project_id=project.id))
        assert res.status_code == 302
        assert project.progress == 0

        # Boost the project
        res = testapp.get(url_for("project.project_boost", project_id=project.id))
        form = res.forms["projectBoost"]
        form["note"] = "Glorious purpose"
        form["boost_type"] = "Award"
        res = form.submit()
        assert "Award" in res.text

        # Post a drib
        res = testapp.get(url_for("project.project_post", project_id=project.id))
        form = res.forms["projectPost"]
        form["note"] = "Testing"
        res = form.submit().follow()
        assert "Testing" in res.text

        # Post a comment
        project.image_url = ""
        project.save()
        res = testapp.get(url_for("project.project_comment", project_id=project.id))
        form = res.forms["projectPost"]
        form["note"] = "Commenting ![](img.jpg)"
        res = form.submit().follow()
        assert "Commenting" in res.text
        # NO auto-images for a comment
        assert project.image_url == ""

        # Test auto-images
        res = testapp.get(url_for("project.project_post", project_id=project.id))
        form = res.forms["projectPost"]
        form["note"] = "This ![](http://img.jpg) is a picture"
        assert project.image_url == ""
        res = form.submit().follow()
        assert "img.jpg" in project.image_url
