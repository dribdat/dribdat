# -*- coding: utf-8 -*-
"""Application assets."""
from flask_assets import Bundle, Environment

assets = Environment()

def compile_assets(config):
    """Configure and build asset bundles."""

    theme = config["DRIBDAT_THEME"]
    theme = 'bootswatch/%s' % theme.lower() if theme else 'bootstrap/css'

    css = Bundle(
        "libs/%s/bootstrap.min.css" % theme,
        "libs/FlipClock/flipclock.css",
        "css/honeycomb.css",
        "css/timeline.css",
        "css/style.css",
        filters="cssmin",
        output="public/css/common.css"
    )

    js = Bundle(
        "libs/jquery/jquery.min.js",
        "libs/popper.js/umd/popper.min.js",
        "libs/bootstrap/js/bootstrap.min.js",
        "js/plugins.js",
        "js/script.js",
        "libs/FlipClock/flipclock.min.js",
        "js/clock.js",
        filters='jsmin',
        output="public/js/common.js"
    )

    assets.register('js_all', js)
    assets.register('css_all', css)
