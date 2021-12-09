# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField, BooleanField,
    StringField, PasswordField,
    TextAreaField,
    SelectMultipleField,
    SelectField, HiddenField,
    TimeField, DateField,
)
from wtforms.fields.html5 import (
    URLField, EmailField,
)
from wtforms.validators import DataRequired, length
from ..user.validators import UniqueValidator
from dribdat.user.models import User, Project, Event

from datetime import time, datetime


class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False
        self.user = User.query.filter_by(username=self.username.data).first()
        if not self.user:
            self.username.errors.append('Unknown username')
            return False
        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False
        # Inactive users are allowed to log in, but not much else.
        return True


class UserForm(FlaskForm):
    id = HiddenField('id')
    roles = SelectMultipleField(
        u'Roles', coerce=int,
        description="Choose one or more team roles for yourself.")
    webpage_url = URLField(
        u'Online profile', [length(max=128)],
        description="Link to your website or a social media profile.")
    my_story = TextAreaField(
        u'My story',
        description="A brief bio and outline of the competencies you bring "
        + "into the mix. The top portion of your profile.")
    my_goals = TextAreaField(
        u'My goals',
        description="What brings you here? Share a few words about your "
        + "interests. This is the bottom portion of your profile.")
    username = StringField(
        u'Username', [length(max=25), UniqueValidator(
            User, 'username'), DataRequired()],
        description="Short and sweet.")
    email = EmailField(
        u'E-mail address', [length(max=80), DataRequired()],
        description="For a profile image, link this address at Gravatar.com")
    password = PasswordField(
        u'Change password', [length(max=128)],
        description="Leave blank to keep your password as it is.")
    submit = SubmitField(u'Save changes')


class ProjectNew(FlaskForm):
    id = HiddenField('id')
    autotext_url = URLField(
        u'Readme', [length(max=2048)],
        description="[Optional] URL to a repository or online documentation "
        + "of your project.")
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), DataRequired()],
        description=u"A short project title or team name - you may change "
        + "this later.")
    summary = StringField(
        u'Summary', [length(max=140)],
        description="The headline of your project, in up to 140 characters.")
    category_id = SelectField(
        u'Category', coerce=int, description=u"Select the category that your "
        + " challenge addresses.")
    contact_url = StringField(
        u'Contact', [length(max=2048)],
        description="On which channel, or in which room, to find you.")
    # longtext = TextAreaField(u'Describe your idea')
    submit = SubmitField(u'Save')


class ProjectForm(FlaskForm):
    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Project, 'name'), DataRequired()],
        description="[Required] A short project name, max 80 characters.")
    summary = StringField(
        u'Summary', [length(max=140)],
        description="The headline of your project, in up to 140 characters.")
    longtext = TextAreaField(
        u'Pitch',
        description="To format, use Markdown or HTML. Links on their "
        + "own line may get rich previews.")
    webpage_url = URLField(
        u'Project link', [length(max=2048)],
        description="URL to a live demo, presentation, or a link to get "
        + "more information.")
    is_webembed = BooleanField(u'Embed this link directly on project page')
    category_id = SelectField(u'Challenge category', coerce=int)
    submit = SubmitField(u'Save changes')


class ProjectDetailForm(FlaskForm):
    id = HiddenField('id')
    autotext_url = URLField(
        u'Readme', [length(max=255)],
        description="URL to external documentation "
        + "(code repository, online doc,..)")
    source_url = URLField(
        u'Sources', [length(max=255)],
        description="URL of your source code repository or project data.")
    download_url = URLField(
        u'Download', [length(max=255)],
        description="URL to a release page, website, app store,.. "
        + " where your project may be installed.")
    contact_url = StringField(
        u'Contact us', [length(max=255)],
        description="URL of an issues page, contact form, chat channel, "
        + "forum thread, social media account,..")
    # Note: relative links allowed in image_url -> StringField
    image_url = StringField(
        u'Cover image', [length(max=255)],
        description="URL of an image to display at the top of the page.")
    logo_color = StringField(
        u'Color scheme', [length(max=7)],
        description="Customize the color of your project page.")
    # logo_icon = StringField(u'<a target="_blank" href="
    # http://fontawesome.io/icons/#search">Custom icon</a>',
    #     [length(max=20)], description="A FontAwesome icon")
    submit = SubmitField(u'Save changes')


class ProjectPost(FlaskForm):
    id = HiddenField('id')
    has_progress = BooleanField(u"Let's go")
    note = TextAreaField(
        u'What are you working on right now?',
        [length(max=280), DataRequired()],
        description=u'A short note for your project log.')
    submit = SubmitField(u'Save post')


class ProjectComment(FlaskForm):
    id = HiddenField('id')
    note = TextAreaField(
        u'Comments and reviews',
        [length(max=280), DataRequired()],
        description=u'A suggestion or constructive feedback for the team.'
                    + ' Please note the Code of Conduct.')
    submit = SubmitField(u'Save comment')


class ProjectBoost(FlaskForm):
    id = HiddenField('id')
    note = TextAreaField(u'Short praise and comments', [
                         length(max=140), DataRequired()])
    boost_type = SelectField(u'Select booster pack', [DataRequired()])
    submit = SubmitField(u'Energize!')


class NewEventForm(FlaskForm):
    next = HiddenField()
    id = HiddenField('id')
    name = StringField(
        u'Title',
        [length(max=80), UniqueValidator(Event, 'name'), DataRequired()])
    starts_date = DateField(u'Starts date', default=datetime.now())
    starts_time = TimeField(u'Starts time', default=time(9, 0, 0))
    ends_date = DateField(u'Finish date', default=datetime.now())
    ends_time = TimeField(u'Finish time', default=time(16, 0, 0))
    summary = StringField(
        u'Summary',
        [length(max=140)],
        description=u'A short overview (140 chars) of the upcoming event')
    hostname = StringField(
        u'Hosted by', [length(max=80)],
        description=u'Organization responsible for the event')
    location = StringField(
        u'Located at', [length(max=255)],
        description=u'The event locale or virtual space')
    description = TextAreaField(
        u'Description', description=u'Markdown and HTML supported')
    logo_url = URLField(
        u'Host logo link', [length(max=255)],
        description=u'Link to a logo file, ideally square, max res 512x512')
    webpage_url = URLField(
        u'Home page link', [length(max=255)],
        description=u'Link to register and get information about the event')
    community_url = URLField(
        u'Community link', [length(max=255)],
        description=u'Link to connect to a community forum or hashtag')
    submit = SubmitField(u'Save')
