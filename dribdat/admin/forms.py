# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import (
    HiddenField, SubmitField, RadioField, DateField,
    StringField, PasswordField, SelectMultipleField,
    TextField
)
from wtforms.validators import AnyOf, required, length

from ..user import USER_ROLE, USER_STATUS

class UserForm(Form):
    next = HiddenField()
    username = StringField(u'Username', [required(), length(max=80)])
    first_name = StringField(u'First name', [length(max=30)])
    last_name = StringField(u'Last name', [length(max=30)])
    email = StringField(u'E-mail', [required(), length(max=80)])
    password = PasswordField(u'New password')
    is_admin = RadioField(u"Role", [AnyOf([str(val) for val in USER_ROLE.keys()])],
            choices=[(str(val), label) for val, label in USER_ROLE.items()])
    active = RadioField(u"Status", [AnyOf([str(val) for val in USER_STATUS.keys()])],
            choices=[(str(val), label) for val, label in USER_STATUS.items()])
    #created_time = DateField(u'Created time')
    submit = SubmitField(u'Save')
