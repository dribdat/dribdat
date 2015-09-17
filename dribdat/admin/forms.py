# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import (
    HiddenField, SubmitField, BooleanField,
    StringField, PasswordField, SelectField,
    TextAreaField
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
    is_admin = BooleanField(u"Administrator", default=False)
    active = BooleanField(u"Active", default=True)
    submit = SubmitField(u'Save')

class EventForm(Form):
    next = HiddenField()
    name = StringField(u'Title', [required(), length(max=80)])
    description = TextAreaField(u'Description')
    webpage_url = StringField(u'Home page link', [length(max=255)])
    starts_at = DateField(u'Starts at')
    ends_at = DateField(u'Finishes at')
    submit = SubmitField(u'Save')

class ProjectForm(Form):
    next = HiddenField()
    name = StringField(u'Title', [required(), length(max=80)])
    summary = StringField(u'Short summary (140 chars)', [length(max=140)])
    webpage_url = StringField(u'Project home link', [length(max=255)])
    source_url = StringField(u'Source code link', [length(max=255)])
    image_url = StringField(u'Banner image link', [length(max=255)])
    event_id = SelectField(u"Event", coerce=int)
    submit = SubmitField(u'Save')
