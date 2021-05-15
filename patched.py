# -*- coding: utf-8 -*-
"""Monkey patched application for workers."""
try:
    from eventlet import monkey_patch as monkey_patch
    monkey_patch()
except ImportError:
    try:
        from gevent.monkey import patch_all
        patch_all()
        from psycogreen.gevent import patch_psycopg
        patch_psycopg()
    except ImportError:
        pass

from dribdat.app import init_app  # re-export
