# -*- coding: utf-8 -*-
"""Test configs."""
from dribdat.app import init_app
from dribdat.settings import DevConfig, ProdConfig


def test_production_config():
    """Production config."""
    app = init_app(ProdConfig)
    assert app.config['ENV'] == 'prod'
    assert app.config['DEBUG'] is False
    assert app.config['DEBUG_TB_ENABLED'] is False
    assert app.config['ASSETS_DEBUG'] is False


def test_dev_config():
    """Development config."""
    app = init_app(DevConfig)
    assert app.config['ENV'] == 'dev'
    assert app.config['DEBUG'] is True
    assert app.config['ASSETS_DEBUG'] is True
