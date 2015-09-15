# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import (
    HiddenField, SubmitField, RadioField,
    StringField, PasswordField, SelectField,
    TextField
)
from wtforms.validators import AnyOf, required, length
from wtforms.fields.html5 import DateField

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
    submit = SubmitField(u'Save')

class EventForm(Form):
    next = HiddenField()
    name = StringField(u'Title', [required(), length(max=80)])
    description = StringField(u'Description', [length(max=140)])
    webpage_url = StringField(u'Home page link', [length(max=255)])
    starts_at = DateField(u'Starts at')
    ends_at = DateField(u'Finishes at')
    submit = SubmitField(u'Save')

class ProjectForm(Form):
    next = HiddenField()
    name = StringField(u'Title', [required(), length(max=80)])
    summary = StringField(u'Description', [length(max=140)])
    image_url = StringField(u'Banner image link', [length(max=255)])
    webpage_url = StringField(u'Home page link', [length(max=255)])
    event_id = SelectField(u"Event", coerce=int)
    submit = SubmitField(u'Save')
