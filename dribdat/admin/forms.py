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
    hostname = StringField(u'Hosted by', [length(max=80)])
    location = StringField(u'Located at', [length(max=255)])
    description = TextAreaField(u'Description')
    logo_url = StringField(u'Host logo link', [length(max=255)])
    webpage_url = StringField(u'Home page link', [length(max=255)])
    community_url = StringField(u'Community link', [length(max=255)])
    community_embed = TextAreaField(u'Community embed code')
    starts_at = DateField(u'Starts at')
    ends_at = DateField(u'Finishes at')
    submit = SubmitField(u'Save')

class ProjectForm(Form):
    next = HiddenField()
    event_id = SelectField(u'Event', coerce=int)
    name = StringField(u'Title', [required(), length(max=80)])
    summary = StringField(u'Short summary (120 chars)', [length(max=120)])
    longtext = TextAreaField(u'Full description (or cache)')
    autotext_url = StringField(u"Auto-update link", [length(max=255)])
    webpage_url = StringField(u'Project home link', [length(max=255)])
    source_url = StringField(u'Source code link', [length(max=255)])
    image_url = StringField(u'Banner image link', [length(max=255)])
    submit = SubmitField(u'Save')
