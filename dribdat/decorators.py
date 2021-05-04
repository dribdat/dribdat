# -*- coding: utf-8 -*-

from functools import wraps

from flask import abort, jsonify
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.active or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_allowed:
            return jsonify(flag='fail', msg='Login required')
        return f(*args, **kwargs)
    return decorated
