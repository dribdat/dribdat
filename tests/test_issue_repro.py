import pytest
import pickle
from flask import Flask, jsonify, send_file
import tempfile
import os
from dribdat.public.api import generate_event_package
from dribdat.user.models import Event
from tests.factories import EventFactory

@pytest.mark.usefixtures('db')
class TestCacheIssue:
    def test_generate_event_package_json_picklable(self, app):
        event = EventFactory()
        event.save()
        with app.test_request_context():
            resp = generate_event_package(event, format='json')
            # resp is a Response object from jsonify.
            # We want to make sure the data we put into cache is picklable.
            # In our implementation, we cache package.to_dict()
            from dribdat.extensions import cache
            cache_key = f"event_package_{event.id}_json"
            cached_data = cache.get(cache_key)
            assert cached_data is not None
            pickle.dumps(cached_data) # Should not raise

    def test_generate_event_package_zip_works(self, app):
        event = EventFactory()
        event.save()
        with app.test_request_context():
            resp = generate_event_package(event, format='zip')
            # resp is a Response object from send_file.
            # It should contain a BufferedReader which is NOT picklable.
            # But since we removed @cache.cached(), it shouldn't be pickled.
            assert resp.status_code == 200

            try:
                pickle.dumps(resp)
                # It might still be unpicklable, but that's fine as long as
                # Flask-Caching doesn't try to pickle it.
            except Exception as e:
                print(f"Confirmed: ZIP response is still unpicklable: {e}")
