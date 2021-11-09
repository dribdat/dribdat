# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import (
    HiddenField, SubmitField, BooleanField,
    StringField, PasswordField, SelectField,
    TextAreaField, RadioField, IntegerField,
)
from wtforms.fields.html5 import (
    DateField, TimeField,
    URLField, EmailField,
)
from wtforms.validators import DataRequired, length

from datetime import time, datetime

from dribdat.user.models import User, Project, Event, Role, Resource
from ..user.validators import UniqueValidator
from ..user import projectProgressList, resourceTypeList
from wtforms import (
    SelectMultipleField,
)

class UserForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    username = StringField(
        u'Username',
        [length(max=80), UniqueValidator(User, 'username'), DataRequired()])
    email = EmailField(u'E-mail address', [length(max=80), DataRequired()])
    password = PasswordField(u'New password (optional)', [length(max=128)])
    is_admin = BooleanField(u"Administrator", default=False)
    active = BooleanField(u"Active", default=True)
    submit = SubmitField(u'Save')

class UserProfileForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    roles = SelectMultipleField(u'Roles', coerce=int)
    webpage_url = URLField(u'Online profile', [length(max=128)])
    my_story = TextAreaField(u'My story')
    my_goals = TextAreaField(u'My goals')
    submit = SubmitField(u'Save')

class EventForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Event, 'name'), DataRequired()])
    is_current = BooleanField(
        u'Featured', default=False,
        description=u'📣 Pin this event to the top of the homepage.')
    is_hidden = BooleanField(
        u'Hidden', default=False,
        description=u'🚧 This event is not shown on the homepage.')
    lock_editing = BooleanField(
        u'Freeze projects', default=False,
        description=u'🔒 Prevent users editing any projects.')
    lock_starting = BooleanField(
        u'Lock projects', default=False,
        description=u'🔒 Block starting new projects here.')
    lock_resources = BooleanField(
        u'Resource area', default=False,
        description=u'💡 Used as toolbox, ignoring start and finish.')
    starts_date = DateField(u'Starts date', default=datetime.now())
    starts_time = TimeField(u'Starts time', default=time(9, 0, 0))
    ends_date = DateField(u'Finish date', default=datetime.now())
    ends_time = TimeField(u'Finish time', default=time(16, 0, 0))
    summary = StringField(
        u'Summary',
        [length(max=140)],
        description=u'A short overview (140 chars) of the upcoming event')
    hostname = StringField(
        u'Hosted by',
        [length(max=80)],
        description=u'Organization responsible for the event')
    location = StringField(
        u'Located at',
        [length(max=255)],
        description=u'The event locale or virtual space')
    description = TextAreaField(
        u'Description',
        description=u'Markdown and HTML supported')
    logo_url = URLField(
        u'Host logo link',
        [length(max=255)],
        description=u'URL to an (ideally) square and max 512x512 pixel image')
    webpage_url = URLField(
        u'Home page link',
        [length(max=255)],
        description=u'Link to register or get more info about the event')
    community_url = URLField(
        u'Community link',
        [length(max=255)],
        description=u'Link to connect to a community forum or hashtag')
    certificate_path = URLField(
        u'Certificate link',
        [length(max=1024)],
        description='Include {username}, {email} or {sso} identifier '
        + 'in your participant certificate generator')
    instruction = TextAreaField(
        u'Instructions',
        description=u'Shown to participants on the Resources page - '
        + 'Markdown and HTML supported')
    boilerplate = TextAreaField(
        u'Getting started guide',
        description=u'Top of new project page, markdown and HTML supported')
    community_embed = TextAreaField(
        u'Code of conduct and community links',
        description=u'Bottom of event and project page: Markdown, HTML and '
        + 'embedded scripts are supported')
    custom_css = TextAreaField(
        u'Custom stylesheet',
        description=u'For external CSS: @import url(https://...);')
    submit = SubmitField(u'Save')


class ProjectForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    user_name = StringField(u'Started by')
    event_id = SelectField(u'Event', coerce=int)
    category_id = SelectField(u'Challenge category', coerce=int)
    progress = SelectField(u'Progress', coerce=int,
                           choices=projectProgressList())
    hashtag = StringField(
        u'Hashtag',
        [length(max=255)],
        description="Uniquely identifies the team channel")
    autotext_url = URLField(
        u'Readme',
        [length(max=2048)],
        description="Location from which to Sync content")
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), DataRequired()])
    summary = StringField(u'Short summary', [length(max=140)])
    longtext = TextAreaField(u'Description')
    autotext = TextAreaField(u'Readme content')
    webpage_url = URLField(u'Presentation or demo link', [length(max=2048)])
    is_webembed = BooleanField(u'Embed contents of demo link', default=False)
    contact_url = URLField(u'Contact link', [length(max=2048)])
    source_url = URLField(u'Source link', [length(max=2048)])
    download_url = URLField(u'Download link', [length(max=2048)])
    image_url = URLField(u'Image link', [length(max=255)])
    logo_color = StringField(u'Custom color', [length(max=7)])
    logo_icon = StringField(u'Custom icon', [length(max=20)])
    submit = SubmitField(u'Save')


class CategoryForm(FlaskForm):
    next = HiddenField()
    name = StringField(u'Name', [length(max=80), DataRequired()])
    description = TextAreaField(u'Description',
                                description=u'Markdown and HTML supported')
    logo_color = StringField(u'Custom color', [length(max=7)])
    logo_icon = StringField(u'Custom icon (fontawesome.io/icons)',
                            [length(max=20)])
    event_id = SelectField(u'Specific to an event, or global if blank',
                           coerce=int)
    submit = SubmitField(u'Save')


class RoleForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    name = StringField(
        u'Name',
        [length(max=80), UniqueValidator(Role, 'name'), DataRequired()])
    submit = SubmitField(u'Save')


class ResourceForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    name = StringField(
        u'Name',
        [length(max=80), UniqueValidator(Resource, 'name'), DataRequired()])
    project_id = IntegerField(u'Project id')
    type_id = RadioField(u'Type', coerce=int, choices=resourceTypeList())
    source_url = URLField(
        u'Link',
        [length(max=2048)], description=u'URL to get more information')
    content = TextAreaField(
        u'Comment',
        description=u'Describe this resource in more detail')
    progress_tip = SelectField(
        u'Recommended at',
        coerce=int,
        choices=projectProgressList(True, True),
        description=u'Progress level at which to suggest this to teams')
    is_visible = BooleanField(u'Approved and visible to participants')
    submit = SubmitField(u'Save')
