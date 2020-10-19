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
    email = StringField(u'E-mail address', [required(), length(max=80)])
    webpage_url = StringField(u'Online profile', [length(max=128)],
        description="Link to a website or social media profile.")
    password = PasswordField(u'New password (optional)', [length(max=128)])
    submit = SubmitField(u'Save changes')

class ProjectNew(FlaskForm):
    id = HiddenField('id')
    autotext_url = StringField(u'Sync', [length(max=255)],
        description="URL to external source of documentation in GitLab, GitHub, Bitbucket, Data Package or Website")
    name = StringField(u'Title', [required(), length(max=80), UniqueValidator(Project, 'name')],
        description="[Required] a short project name, max 80 characters - you may change this later")
    summary = StringField(u'Summary', [length(max=120)],
        description="Max 120 characters")
    contact_url = StringField(u'Contact link', [length(max=255)],
        description="How best to contact your team")
    category_id = SelectField(u'Challenge category', coerce=int)
    submit = SubmitField(u'Save')

class ProjectForm(FlaskForm):
    id = HiddenField('id')
    # is_autoupdate = BooleanField(u'Sync project data')
    name = StringField(u'Title', [required(), length(max=80), UniqueValidator(Project, 'name')],
        description="[Required] a short project name, max 80 characters")
    summary = StringField(u'Summary', [length(max=120)],
        description="Max 120 characters")
    longtext = TextAreaField(u'Description',
        description="Plain text, Markdown or HTML to describe your project. Use a service like pixelfed.org or imgur.com to upload images")
    webpage_url = StringField(u'Project link', [length(max=2048)],
        description="URL to a live demo, presentation, or link to further information")
    is_webembed = BooleanField(u'Embed project link')
    autotext_url = StringField(u'Sync', [length(max=255)],
        description="URL to external source of documentation in GitLab, GitHub, Bitbucket, Data Package or Web site")
    source_url = StringField(u'Source link', [length(max=255)],
        description="URL of your repository")
    contact_url = StringField(u'Contact link', [length(max=255)],
        description="URL of an issues page, forum thread, chat channel, e-mail, hashtag, ...")
    image_url = StringField(u'Image link', [length(max=255)],
        description="URL to an image to display at the top")
    logo_color = StringField(u'Custom color', [length(max=7)],
        description="Background color of your project page")
    # logo_icon = StringField(u'<a target="_blank" href="http://fontawesome.io/icons/#search">Custom icon</a>',
    #     [length(max=20)], description="A FontAwesome icon for the project browser.")
    category_id = SelectField(u'Challenge category', coerce=int)
    submit = SubmitField(u'Save changes')

class ProjectPost(FlaskForm):
    id = HiddenField('id')
    progress = SelectField(u'Progress', coerce=int)
    note = TextAreaField(u'Note', [required(), length(max=140)],
        description="What are you working on right now?")
    submit = SubmitField(u'Submit')
