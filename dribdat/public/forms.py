# -*- coding: utf-8 -*-
"""Public facing forms."""

from flask_wtf import FlaskForm
from wtforms import (
    SubmitField, BooleanField,
    StringField, TextAreaField,
    SelectField, HiddenField,
)
from wtforms.fields import (
    TimeField, DateField,
    URLField, DateTimeLocalField
)
# from wtforms_html5 import AutoAttrMeta
from wtforms.validators import InputRequired, length
from ..user.validators import UniqueValidator
from dribdat.user.models import Project, Event
from datetime import time, datetime, timedelta


class ProjectImport(FlaskForm):
    """Import a project from a repostiroy."""

    id = HiddenField('id')
    autotext_url = URLField(
        u'Readme', [length(max=2048)],
        description="Paste link to a code repository or document")
    name = HiddenField(u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), InputRequired()])
    submit = SubmitField(u'Import')


class ProjectNew(FlaskForm):
    """Create a project form."""

    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), InputRequired()],
        description=u"A short team or project name - you may change "
        + "this later.")
    summary = TextAreaField(
        u'Summary', [length(max=2048)],
        render_kw={'maxlength': 2048, 'rows': 3},
        description="A short, plain-text description of your project or challenge.")
    generate_pitch = BooleanField(u"🅰️ℹ️ Propose a challenge text based on my title and summary")
    category_id = SelectField(
        u'Category', coerce=int, description=u"Select the category that your "
        + " challenge addresses.")
    contact_url = StringField(
        u'Contact', [length(max=2048)],
        description="On which channel, or in which room, to find you.")
    template = HiddenField('template')
    submit = SubmitField(u'Save')


class ProjectForm(FlaskForm):
    """Edit a project form."""

    id = HiddenField('id')
    summary = StringField(
        u'Summary', [length(max=2048)],
        render_kw={'maxlength': 2048, 'rows': 3},
        description="A short, plain-text description of your topic.")
    webpage_url = URLField(
        u'Presentation', [length(max=2048)],
        description="URL to a live demo, presentation, or a link to get "
        + "more information.")
    is_webembed = BooleanField(u'Embed the Presentation on page')
    longtext = TextAreaField(
        u'Pitch', [length(max=64000)],
        description="Markdown supported. Put a link"
        + " to supported sites (SpeakerDeck, YouTube,..) on a line for a preview."
        + " No copypasta - use the 'Upload Image' button.")
    autotext_url = URLField(
        u'Readme link', [length(max=255)],
        description="URL to a code repository, document, or wiki to Sync with. 💡 Tips: dribdat.cc/sync")
    note = TextAreaField(
        u'What changed?',
        [length(max=280)],
        render_kw={'maxlength': 280, 'rows': 3},
        description=u'(Optional) A short update for the project log')
    submit = SubmitField(u'Save changes')
    is_minoredit = BooleanField(u'This is a minor edit') # No log entry if checked


class ProjectDetailForm(FlaskForm):
    """Edit a project detail form."""

    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), InputRequired()],
        render_kw={'maxlength': 80, 'required': 'required'},
        description="A short name for your project or challenge.")
    source_url = URLField(
        u'Source', [length(max=255)],
        description="Link to the original source code of your project.")
    # Note: contact_url could be an e-mail or room number -> StringField
    contact_url = StringField(
        u'Contact', [length(max=255)],
        description="How to reach you via website or e-mail.")
    download_url = URLField(
        u'Demo', [length(max=255)],
        description="Link to online demo or download area for this project.")
    hashtag = StringField(
        u'Affiliation', [length(max=140)],
        description="Your organization, channel, or social media hashtag.")
    # Note: relative links allowed in image_url -> StringField
    image_url = StringField(
        u'Cover image', [length(max=255)],
        description="Link to an image showing in the project overview and at the top of the page.")
    logo_color = StringField(
        u'Outline color',
        description="Customize the color scheme of your project page.")
    logo_icon = StringField(
        u'Named icon',
        [length(max=20)], description='Select an icon from FontAwesome'
        + ': https://fontawesome.com/v4/cheatsheet')
    category_id = SelectField(u'Challenge category', coerce=int,
        description="If available, which category does your project belong to?")
    submit = SubmitField(u'Save changes')


class ProjectPost(FlaskForm):
    """Add a post to a project."""

    id = HiddenField('id')
    has_progress = BooleanField(u"Level up")
    note = TextAreaField(
        'How are the vibes in your team right now?',
        [length(max=280), InputRequired()],
        render_kw={'maxlength': 280, 'minlength': 4},
        description=u'A short note for your project log.')
    submit = SubmitField(u'Save post',
        render_kw={'data-toggle': "modal", 'data-target': "#pleasewaitModal"})


class ProjectComment(FlaskForm):
    """Add a comment to a project."""

    id = HiddenField('id')
    note = TextAreaField(
        u'Comments and reviews',
        [length(max=280), InputRequired()],
        render_kw={'maxlength': 280, 'minlength': 4},
        description=u'A suggestion or constructive feedback for the team.'
                    + ' Please note the Code of Conduct.')
    submit = SubmitField(u'Save comment',
        render_kw={'data-toggle': "modal", 'data-target': "#pleasewaitModal"})


class ProjectBoost(FlaskForm):
    """Add a boost to a project."""

    id = HiddenField('id')
    note = TextAreaField(u'Short praise and comments', [
                         length(max=280), InputRequired()])
    boost_type = SelectField(u'Select a booster pack', [InputRequired()])
    submit = SubmitField(u'Energize!')


class EventNew(FlaskForm):
    """Add a new Event."""

    next = HiddenField()
    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Event, 'name'), InputRequired()])
    starts_at = DateTimeLocalField(u'Starting', [InputRequired()])
    ends_at = DateTimeLocalField(u'Finishing', [InputRequired()])
    summary = StringField(
        u'Summary',
        [length(max=140)],
        description=u'A short overview of the upcoming event')
    hostname = StringField(
        u'Hosted by', [length(max=80)],
        description=u'Organization responsible for the event')
    location = StringField(
        u'Located at', [length(max=255)],
        description=u'The event locale or virtual space')
    hashtags = StringField(
        u'Hashtags', [length(max=255)],
        description=u'Social media hashtags for this event')
    description = TextAreaField(
        u'Description', description=u'Markdown and HTML supported')
    logo_url = URLField(
        u'Host logo link', [length(max=255)],
        description=u'Link to a small logo file (max 688x130)')
    gallery_url = URLField(
        u'Gallery links',
        [length(max=2048)],
        description=u'URL to large background image (max 1920x1080)')
    webpage_url = URLField(
        u'Home page link', [length(max=255)],
        description=u'Link to register and get information about the event')
    community_url = URLField(
        u'Community link', [length(max=255)],
        description=u'Link to connect to a community forum or hashtag')
    submit = SubmitField(u'Save')
