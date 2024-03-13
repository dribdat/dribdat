# -*- coding: utf-8 -*-
"""Dribdat feature tests using WebTest.

See: http://webtest.readthedocs.org/
"""
from flask import url_for
from .factories import ProjectFactory, EventFactory, UserFactory
from dribdat.onebox import make_onebox
from dribdat.public.projhelper import resources_by_stage, project_action
from dribdat.aggregation import ProjectActivity
from dribdat.utils import load_yaml_presets
from dribdat.apifetch import FetchStageConfig
from dribdat.user.constants import PR_CHALLENGE


STAGES_URL = 'https://raw.githubusercontent.com/dribdat/dribdat/main/dribdat/templates/includes/stages.yaml'


class TestFeatures:
    """Project features."""

    def test_onebox(self, project, testapp):
        """Generate one box."""
        srv = url_for('public.home', _external=True)
        url = "%sproject/%d" % (srv, project.id)
        test_markdown = """Some project content
<p><a href="%s">%s</a></p>
EOF""" % (url, url)
        result = make_onebox(test_markdown)
        assert 'onebox' in result

    def test_project_api(self, project, testapp):
        """Make sure Project APIs respond correctly."""
        project = ProjectFactory()
        project.name = 'example'
        project.longtext = 'Word.'
        project.autotext = 'some test readme content'
        project.save()
        # print(project.data)
        assert 'example' in project.data['name']
        assert project.data['excerpt'] == ''
        project.autotext_url = 'https:/...'
        assert 'test' in project.autotext
        assert 'test' in project.data['excerpt']
        # test stats
        stats = project.get_stats()
        assert stats['total'] == 0
        assert stats['updates'] == 0
        assert stats['commits'] == 0
        assert stats['during'] == 0
        assert stats['people'] == 0
        assert stats['sizepitch'] == 5
        assert stats['sizetotal'] == 48

    def test_custom_stages(self):
        """Load custom event stages."""
        stages_local = load_yaml_presets('stages')
        assert len(stages_local) == 7
        assert 'CHALLENGE' in stages_local
        assert int(stages_local['CHALLENGE']['id']) == PR_CHALLENGE
        stages_remote = FetchStageConfig(STAGES_URL)
        assert len(stages_remote) == 7
        assert 'CHALLENGE' in stages_remote
        assert int(stages_remote['CHALLENGE']['id']) == PR_CHALLENGE

    def test_project_stage(self, project, testapp):
        """Check stage progression."""
        event = EventFactory()
        event.lock_resources = True
        event.hidden = False
        event.save()
        project = ProjectFactory()
        project.name = 'example resource'
        project.save()
        assert resources_by_stage(0) == []
        project.event_id = event.id
        project.progress = 0
        project.is_hidden = False
        assert project.is_challenge
        project.save()
        assert len(resources_by_stage(0)) == 1
        assert project_action(project.id)

    def test_participant_search(self, user, testapp):
        """Search for participants."""
        res = testapp.get('/participants')
        form = res.forms[0]
        # Search for a user that doesn't exist
        form['q'] = '@ibraci'
        res = form.submit()
        assert res.status_code == 200
        assert 'No matches' in res
        # Create a user and search it
        user1 = UserFactory()
        user1.username = 'abracadabra'
        user1.save()
        form = res.forms[0]
        form['q'] = '@abraca'
        res = form.submit()
        assert res.status_code == 200
        assert 'abracadabra' in res
        # Try the same, with an event
        event = EventFactory()
        event.save()
        res = testapp.get('/event/%d/participants' % event.id)
        assert res.status_code == 200
        assert 'No matches' in res
        project = ProjectFactory()
        project.event_id = event.id
        project.save()
        assert ProjectActivity(project, 'star', user1)
        assert not ProjectActivity(project, 'star', user1)
        res = testapp.get('/event/%d/participants' % event.id)
        assert res.status_code == 200
        assert 'abracadabra' in res
        assert ProjectActivity(project, 'unstar', user1)
        assert not ProjectActivity(project, 'unstar', user1)
