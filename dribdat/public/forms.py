# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField, BooleanField,
    StringField, PasswordField,
    TextAreaField,
    SelectField, HiddenField,
    RadioField
)
from wtforms.validators import DataRequired, AnyOf, required, length
from ..user.validators import UniqueValidator
from dribdat.user.models import User, Project

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
        if not self.user.active:
            self.username.errors.append('User not activated')
            return False
        return True

class UserForm(FlaskForm):
    id = HiddenField('id')
    username = StringField(u'Username', [required(), length(max=80), UniqueValidator(User, 'username')])
    email = StringField(u'E-mail', [required(), length(max=80)])
    webpage_url = StringField(u'Online profile', [length(max=128)],
        description="Link to a website or social media profile.")
    password = PasswordField(u'New password (optional)', [length(max=128)])
    submit = SubmitField(u'Save changes')

class ProjectNew(FlaskForm):
    id = HiddenField('id')
    autotext_url = StringField(u'Sync', [length(max=255)],
        description="Optional - an external source (GitLab, GitHub, Bitbucket, ..) to fetch project data.")
    name = StringField(u'Title', [required(), length(max=80), UniqueValidator(Project, 'name')],
        description="* Required - max 80 characters - you may change this at any time.")
    summary = StringField(u'Summary', [length(max=120)],
        description="Max 120 characters.")
    category_id = SelectField(u'Category', coerce=int)
    contact_url = StringField(u'Contact link', [length(max=255)],
        description="How to best contact your team.")
    submit = SubmitField(u'Save')

class ProjectForm(FlaskForm):
    id = HiddenField('id')
    autotext_url = StringField(u'Sync', [length(max=255)],
        description="Optional - an external source (GitLab, GitHub, Bitbucket, ..) to fetch project data.")
    # is_autoupdate = BooleanField(u'Sync project data')
    name = StringField(u'Title', [required(), length(max=80), UniqueValidator(Project, 'name')],
        description="* Required - max 80 characters.")
    summary = StringField(u'Summary', [length(max=120)],
        description="Max 120 characters.")
    longtext = TextAreaField(u'Description',
        description="Text, Markdown or HTML to describe your project. Shown above the README, if Sync is used.")
    category_id = SelectField(u'Category', coerce=int)
    webpage_url = StringField(u'Project link', [length(max=2048)],
        description="URL to a live demo, presentation, or link to further information.")
    is_webembed = BooleanField(u'Embed this',
        description="Show contents of project home directly in the project page.")
    source_url = StringField(u'Source link', [length(max=255)],
        description="URL of your repository.")
    contact_url = StringField(u'Contact link', [length(max=255)],
        description="URL of an issues page, forum thread, chat channel, hashtag, etc.")
    image_url = StringField(u'Image link', [length(max=255)],
        description="URL to an image to display at the top of the project page.")
    logo_color = StringField(u'Custom color', [length(max=7)],
        description="A custom background color for your project page.")
    # logo_icon = StringField(u'<a target="_blank" href="http://fontawesome.io/icons/#search">Custom icon</a>',
    #     [length(max=20)], description="A FontAwesome icon for the project browser.")
    submit = SubmitField(u'Save changes')

class ProjectPost(FlaskForm):
    id = HiddenField('id')
    progress = SelectField(u'Progress', coerce=int)
    note = TextAreaField(u'Note',
        description="A brief note describing your status.")
    submit = SubmitField(u'Submit')
