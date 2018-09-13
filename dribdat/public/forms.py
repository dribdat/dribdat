# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField, BooleanField,
    StringField, PasswordField,
    TextAreaField, TextField,
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
        description="URL to website or social profile - GitHub, Twitter supported with cards.")
    password = PasswordField(u'New password', [length(max=128)])
    submit = SubmitField(u'Save changes')

class ProjectForm(FlaskForm):
    id = HiddenField('id')
    category_id = SelectField(u'Category', coerce=int)
    progress = RadioField(u'Progress', coerce=int)
    autotext_url = StringField(u'Remote link', [length(max=255)],
        description="A supported repository from which to fetch project details.")
    is_autoupdate = BooleanField(u'Sync project data')
    name = StringField(u'Title', [required(), length(max=80), UniqueValidator(Project, 'name')],
        description="Required, though you may change this any time.")
    summary = StringField(u'Short summary', [length(max=120)],
        description="Optional, max. 120 characters, appearing at the top of the project page.")
    longtext = TextAreaField(u'Full description',
        description="Use plain text, Markdown or HTML as you wish to document your project.")
    webpage_url = StringField(u'Project home link', [length(max=255)],
        description="Optional - a live demo or information page.")
    source_url = StringField(u'Source code link', [length(max=255)],
        description="Optional - location of your repository.")
    contact_url = StringField(u'Contact link', [length(max=255)],
        description="Optional - hashtag search, issues page, forum thread, chat channel.")
    image_url = StringField(u'Banner image link', [length(max=255)],
        description="Optional - an image to display at the top of the project page.")
    logo_color = StringField(u'Custom color', [length(max=7)],
        description="Optional - hexadecimal background color for your project page.")
    logo_icon = StringField(u'<a target="_blank" href="http://fontawesome.io/icons/#search">Custom icon</a>',
        [length(max=20)], description="Optional - a FontAwesome icon for the project browser.")
    submit = SubmitField(u'Save changes')
