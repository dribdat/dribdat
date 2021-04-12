# -*- coding: utf-8 -*-
"""Application assets."""
from flask_assets import Bundle, Environment

# Configure asset bundles
assets = Environment()

css = Bundle(
    "css/honeycomb.css",
    "css/timeline.css",
    "css/style.css",
    filters="cssmin",
    output="public/css/common.css"
)

js = Bundle(
    "js/plugins.js",
    "js/script.js",
    "js/clock.js",
    filters='jsmin',
    output="public/js/common.js"
)

assets.register('js_all', js)
assets.register('css_all', css)
