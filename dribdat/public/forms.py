# -*- coding: utf-8 -*-
"""Public facing forms."""

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    SubmitField,
    BooleanField,
    StringField,
    TextAreaField,
    SelectField,
    HiddenField,
)
from wtforms.fields import TimeField, DateField, URLField, DateTimeLocalField

# from wtforms_html5 import AutoAttrMeta
from wtforms.validators import InputRequired, DataRequired, length
from dribdat.user.models import Project, Event
from ..user.validators import UniqueValidator, event_date_check, event_time_check
from datetime import time, datetime, timedelta
from dribdat.futures import UTC


class ProjectImport(FlaskForm):
    """Import a project from a repostiroy."""

    id = HiddenField("id")
    autotext_url = URLField(
        "Readme",
        [length(max=2048)],
        description="Paste link to a code repository or public document",
    )
    name = HiddenField(
        "Title", [length(max=80), UniqueValidator(Project, "name"), InputRequired()]
    )
    recaptcha = RecaptchaField()
    submit = SubmitField("Import")


class ProjectNew(FlaskForm):
    """Create a project form."""

    id = HiddenField("id")
    name = StringField(
        "Title",
        [length(max=80), UniqueValidator(Project, "name"), InputRequired()],
        description="A short team or project name - you may change " + "this later.",
    )
    summary = TextAreaField(
        "Summary",
        [length(max=2048)],
        render_kw={"maxlength": 2048, "rows": 3},
        description="A short, plain-text description of your project or challenge.",
    )
    generate_pitch = BooleanField("🅰️ℹ️ Generate an initial challenge")
    category_id = SelectField(
        "Category",
        coerce=int,
        description="Select the category that your " + " challenge addresses.",
    )
    contact_url = StringField(
        "Contact",
        [length(max=2048)],
        description="Your channel, room, or contact address.",
    )
    template = HiddenField("template")
    recaptcha = RecaptchaField()
    submit = SubmitField("Save")


class ProjectForm(FlaskForm):
    """Edit a project form."""

    id = HiddenField("id")
    webpage_url = URLField(
        "Presentation",
        [length(max=2048)],
        description="Link to a shared tool, live demo, or presentation.",
    )
    longtext = TextAreaField("Pitch", [length(max=64000)])
    # description=""
    # + " Links to supported sites on one line get previews."
    # + " No copypasta: use the 'Upload Image' button.")
    is_webembed = BooleanField("📺 Show Pitch in slide mode")
    note = TextAreaField(
        "What changed?",
        [length(max=280)],
        render_kw={"maxlength": 280, "rows": 3},
        description="A short update for the project log",
    )
    submit = SubmitField("Save changes")
    is_minoredit = BooleanField("This is a minor edit")  # No log entry if checked


class ProjectDetailForm(FlaskForm):
    """Edit a project detail form."""

    id = HiddenField("id")
    name = StringField(
        "Title",
        [length(max=80), UniqueValidator(Project, "name"), InputRequired()],
        render_kw={"maxlength": 80, "required": "required"},
        description="🗞️ A short name for your project or challenge.",
    )
    summary = TextAreaField(
        "Summary", [length(max=2048)], render_kw={"maxlength": 2048, "rows": 3},
        description="🍫 A short headline about your team or project."
    )
    autotext_url = URLField(
        "Readme",
        description="💡 URL to a code repository, document, wiki ➭ www.dribdat.cc/sync",
    )
    technai = StringField(
        "Tech stack",
        [length(max=1024)],
        description="🏀 Comma,separated,list of skills or technai involved.",
    )
    download_url = URLField(
        "Demo",
        description="🧀 Link to online demo or download area for this project.",
    )
    source_url = URLField(
        "Source",
        description="🗝️ Link to the source code of your project - not necessarily same as your Readme.",
    )
    terms_reuse = StringField(
        "Terms of reuse",
        [length(max=256)],
        description="📜 Signal how project data may be remixed or used in AI training.",
    )
    # Note: contact_url could be an e-mail or room number -> StringField
    contact_url = StringField(
        "Contact",
        description="📩 How to reach you, e.g. via website or e-mail.",
    )
    hashtag = StringField(
        "Affiliation",
        [length(max=140)],
        description="🧧 Your organization, channel, or social media hashtag.",
    )
    # Note: relative links allowed in image_url -> StringField
    logo_color = StringField(
        "Outline color", description="🎨 Customize the color scheme of your project page."
    )
    logo_icon = StringField(
        "Project icon",
        [length(max=20)],
        description="🐧 Emoji or icon from FontAwesome "
        + "➭ fontawesome.com/v4/cheatsheet",
    )
    image_url = StringField(
        "Cover image",
        description="🖼️ Link to a top image for the project. Posts overwrite this.",
    )
    category_id = SelectField(
        "Challenge category",
        coerce=int,
        description="🎓 If available, which category does your project belong to?",
    )
    submit = SubmitField("Save changes")


class ProjectPost(FlaskForm):
    """Add a post to a project."""

    id = HiddenField("id")
    has_progress = BooleanField("Level up")
    note = TextAreaField(
        "How are the vibes in your team right now?",
        [length(max=1024)],
        render_kw={"maxlength": 1024, "minlength": 4},
    )
    submit = SubmitField("Send")


class ProjectComment(FlaskForm):
    """Add a comment to a project."""

    id = HiddenField("id")
    note = TextAreaField(
        "My question or comment:",
        [length(max=1024)],
        render_kw={"maxlength": 1024, "minlength": 4},
        description="Write a suggestion or some constructive feedback for the team.",
    )
    submit = SubmitField("Send comment")


class ProjectBoost(FlaskForm):
    """Add a boost to a project."""

    id = HiddenField("id")
    note = TextAreaField(
        "Short praise and comments", [length(max=280), InputRequired()]
    )
    boost_type = SelectField("Select a booster pack", [InputRequired()])
    submit = SubmitField("Energize!")


class EventNew(FlaskForm):
    """Add a new Event."""

    next = HiddenField()
    id = HiddenField("id")
    name = StringField(
        "Title", [length(max=80), UniqueValidator(Event, "name"), InputRequired()]
    )
    starts_at = DateTimeLocalField("Starting", [InputRequired()])
    ends_at = DateTimeLocalField("Finishing", [InputRequired()])
    summary = StringField(
        "Summary",
        [length(max=140)],
        description="A short overview of the upcoming event",
    )
    hostname = StringField(
        "Hosted by",
        [length(max=80)],
        description="Organization responsible for the event",
    )
    location = StringField(
        "Located at", [length(max=255)], description="The event locale or virtual space"
    )
    description = TextAreaField(
        "Description", description="Markdown and HTML supported"
    )
    logo_url = URLField(
        "Host logo link",
        [length(max=255)],
        description="Link to a small logo file (max 688x130)",
    )
    gallery_url = URLField(
        "Gallery link",
        [length(max=2048)],
        description="URL to large background image (max 1920x1080)",
    )
    webpage_url = URLField(
        "Home page link",
        [length(max=255)],
        description="Link to register and get information about the event",
    )
    community_url = URLField(
        "Community link",
        [length(max=255)],
        description="Link to connect to a community forum or hashtag",
    )
    hashtags = StringField(
        "Hashtags",
        [length(max=255)],
        description="Social media hashtags for this event",
    )
    submit = SubmitField("Save")


class EventEdit(FlaskForm):
    """Event editing form."""

    next = HiddenField()
    id = HiddenField("id")
    name = StringField(
        "Title", [length(max=80), UniqueValidator(Event, "name"), DataRequired()]
    )
    summary = StringField(
        "Summary",
        [length(max=140)],
        description="A short tagline of the event, in max 140 characters",
    )
    starts_date = DateField(
        "Starting date", [event_date_check], default=datetime.now(UTC)
    )
    starts_time = TimeField("Starting time", [event_time_check], default=time(9, 0, 0))
    ends_date = DateField("Finish date", default=datetime.now(UTC))
    ends_time = TimeField("Finish time", default=time(16, 0, 0))
    description = TextAreaField(
        "Description", description="Markdown and HTML supported"
    )
    hostname = StringField(
        "Hosted by",
        [length(max=80)],
        description="Organization responsible for the event",
    )
    location = StringField(
        "Located at", [length(max=255)], description="The event locale or virtual space"
    )
    instruction = TextAreaField(
        "Instructions",
        description="Shown to registered participants only. "
        + "Markdown and HTML supported. Split with ---",
    )
    aftersubmit = TextAreaField(
        "Submissions guide",
        description="Shown to the team on projects at challenge stage: Markdown and HTML supported",
    )
    logo_url = URLField(
        "Host logo link",
        [length(max=255)],
        description="Image hosted on a hotlinkable website - "
        + "such as imgbox.com (max 688x130)",
    )
    gallery_url = URLField(
        "Gallery links",
        [length(max=2048)],
        description="Larger background image (max 1920x1080)",
    )
    webpage_url = URLField(
        "Home page link",
        [length(max=255)],
        description="Link to register or get more info about the event",
    )
    community_url = URLField(
        "Community link",
        [length(max=255)],
        description="To find others on a community forum or social media",
    )
    hashtags = StringField(
        "Hashtags",
        [length(max=255)],
        description="Social media hashtags for this event",
    )
    submit = SubmitField("Save")
