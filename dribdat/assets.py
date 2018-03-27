# -*- coding: utf-8 -*-
"""Application assets."""
from flask_assets import Bundle, Environment

css = Bundle(
    "libs/bootstrap/css/bootstrap.min.css",
    "libs/FlipClock/flipclock.css",
    "css/honeycomb.css",
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
    filters='jsmin',
    output="public/js/common.js"
)

assets = Environment()

assets.register('js_all', js)
assets.register('css_all', css)
