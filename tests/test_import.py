# -*- coding: utf-8 -*-
"""Dribdat data import export tests."""

from dribdat.user.models import Event, Project, Activity, Role
from dribdat.aggregation import ProjectActivity
from dribdat.apiutils import (
    get_schema_for_user_projects, 
    get_project_list,
    gen_csv,
)
from dribdat.apipackage import (
    event_to_data_package,
    import_event_package, 
    import_project_data, 
)
from .factories import UserFactory


class TestImport:
    """Sample import export."""

    def test_datapackage(self):
        """Create a data package."""
        event = Event(name="Test Event", summary="Just testin")
        event.save()

        role = Role(name="Test Role")
        role.save()

        user = UserFactory(username="Test Author")
        user.roles.append(role)
        user.save()

        proj1 = Project(name="Test Project")
        proj1.event = event
        proj1.user = user
        proj1.save()

        acty1 = Activity("review", proj1.id)
        acty1.content = "Hello World!"
        acty1.save()

        dp_json = event_to_data_package(event, user)
        assert dp_json.title == "Test Event"

        acty1.delete()
        proj1.delete()
        event.delete()

        assert Event.query.filter_by(name="Test Event").count() == 0

        import_event_package(dp_json)
        assert Event.query.filter_by(name="Test Event").count() == 1

    def test_user_schema(self):
        """Test user schema."""
        event = Event(name="Test Event", summary="Just testin")
        event.save()
        user = UserFactory(username="Test Author")
        user.save()

        # Generate importable schema for local host
        hosturl = "https://localhost"

        # Initially just a warning message
        schema = get_schema_for_user_projects(user, hosturl)
        assert 'message' in schema

        # Join a project
        proj1 = Project(name="Test Project")
        proj1.event = event
        proj1.user = user
        proj1.progress = 10
        proj1.save()
        ProjectActivity(proj1, "star", user)

        # Now we are a member of one project
        schema = get_schema_for_user_projects(user, hosturl)
        assert len(schema) == 1
        assert 'message' not in schema
        assert len(schema[0]["workPerformed"]) == 1

        # Create another project
        proj2 = Project(name="Another Project")
        proj2.event = event
        proj2.user = user
        proj2.save()
        ProjectActivity(proj2, "star", user)

        # Now we are a member of two projects
        schema = get_schema_for_user_projects(user, hosturl)
        assert len(schema[0]["workPerformed"]) == 2

        # Clean up
        proj1.delete()
        proj2.delete()
        event.delete()
        user.delete()

    def test_import_export(self):
        """Create an export sample."""
        event = Event(name="Test Event", summary="Just testin")
        event.save()
        user = UserFactory(username="Test Author")
        user.save()
        for p in range(1, 6):
            proj = Project(name="Test Project %d" % p)
            proj.event = event
            proj.user = user
            proj.progress = p * 10
            proj.save()
        testlist = get_project_list(event.id, 'testhost', True)
        assert len(testlist) == 5
        testcsv = gen_csv(testlist)
        assert testcsv.startswith('"id",')
        testimport = import_project_data(testlist, True, event)
        assert len(testimport) == 5
        assert 'Test Project' in testimport[0]['name']

