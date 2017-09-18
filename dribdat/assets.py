# -*- coding: utf-8 -*-
"""Application assets."""
from flask_assets import Bundle, Environment

css = Bundle(
    "css/bootstrap.min.css",
    # "libs/bootstrap/dist/css/bootstrap.min.css",
    "css/honeycomb.css",
    "libs/FlipClock/flipclock.css",
    "css/style.css",
    filters="cssmin",
    output="public/css/common.css"
)

js = Bundle(
    "libs/jQuery/dist/jquery.min.js",
    "libs/popper.js/dist/umd/popper.min.js",
    "libs/bootstrap/dist/js/bootstrap.min.js",
    "js/plugins.js",
    "js/script.js",
    filters='jsmin',
    output="public/js/common.js"
)

assets = Environment()

assets.register('js_all', js)
assets.register('css_all', css)
