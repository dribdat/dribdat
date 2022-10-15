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
from os import environ
from datetime import time, datetime
from dribdat.user.models import User, Project, Event, Role, Resource
from ..user.validators import UniqueValidator
from ..user import projectProgressList, resourceTypeList
from wtforms import (
    SelectMultipleField, ValidationError
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


def event_date_check(form, starts_date):
    ends_date = form.ends_date.data
    if starts_date.data > ends_date:
        raise ValidationError('Start date must not be after end date.')


def event_time_check(form, starts_time):
    ends_time = form.ends_time.data
    starts_date = form.starts_date.data
    ends_date = form.ends_date.data
    if starts_date == ends_date and starts_time.data > ends_time:
        raise ValidationError('Start time must be before end time.')


def get_time_note():
    tz = environ.get('TIME_ZONE', None)
    aware_time = datetime.now().astimezone()
    tzinfo = "The current server time is %s." % aware_time.strftime('%H:%M%z')
    if tz is not None:
        return "%s Time zone: <u title=TIME_ZONE>%s</u>" % (tzinfo, tz)
    return tzinfo


class EventForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Event, 'name'), DataRequired()])
    is_current = BooleanField(
        u'Featured', default=False,
        description=u'📣 Pin this event to the homepage.')
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
    starts_date = DateField(
        u'Starting date', [event_date_check], default=datetime.now())
    starts_time = TimeField(
        u'Starting time',
        [event_time_check], default=time(9, 0, 0),
        description=get_time_note())
    ends_date = DateField(u'Finish date', default=datetime.now())
    ends_time = TimeField(u'Finish time', default=time(16, 0, 0))
    summary = StringField(
        u'Summary',
        [length(max=140)],
        description=u'A short tagline of the event, in max 140 characters')
    hostname = StringField(
        u'Hosted by',
        [length(max=80)],
        description=u'Organization responsible for the event')
    location = StringField(
        u'Located at',
        [length(max=255)],
        description=u'The event locale or virtual space')
    hashtags = StringField(
        u'Hashtags',
        [length(max=255)],
        description=u'Social media hashtags for this event')
    description = TextAreaField(
        u'Description',
        description=u'Markdown and HTML supported')
    logo_url = URLField(
        u'Host logo link',
        [length(max=255)],
        description=u'Image hosted on a hotlinkable website - '
        + 'such as imgbox.com (max 688x130)')
    gallery_url = URLField(
        u'Gallery links',
        [length(max=2048)],
        description=u'Larger background image (max 1920x1080)')
    webpage_url = URLField(
        u'Home page link',
        [length(max=255)],
        description=u'Link to register or get more info about the event')
    community_url = URLField(
        u'Community link',
        [length(max=255)],
        description=u'To find others on a community forum or social media')
    certificate_path = URLField(
        u'Certificate link',
        [length(max=1024)],
        description='Include {username}, {email} or {sso} identifier '
        + 'to generate links to your participant certificate')
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
    category_id = SelectField(u'Category', coerce=int)
    progress = SelectField(u'Progress', coerce=int,
                           choices=projectProgressList())
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), DataRequired()])
    summary = StringField(u'Short summary', [length(max=140)])
    longtext = TextAreaField(u'Description')
    autotext_url = URLField(
        u'Readme',
        [length(max=2048)],
        description="Location from which to Sync content")
    autotext = TextAreaField(u'Readme content')
    webpage_url = URLField(u'Presentation or demo link', [length(max=2048)])
    is_webembed = BooleanField(u'Embed contents of demo link', default=False)
    hashtag = StringField(
        u'Hashtags',
        [length(max=255)],
        description="Team channel or social media hashtag")
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
    logo_icon = StringField(u'Custom icon', [length(max=20)],
                            description=u'fontawesome.com/v5/cheatsheet')
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
