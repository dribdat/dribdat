# -*- coding: utf-8 -*-
"""Application assets."""
from flask_assets import Bundle, Environment

# Configure asset bundles
assets = Environment()

css = Bundle(
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
