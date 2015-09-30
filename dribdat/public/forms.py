# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import (
    SubmitField, BooleanField,
    StringField, PasswordField,
    TextAreaField, TextField,
    SelectField
)
from wtforms.validators import DataRequired

from dribdat.user.models import User
from wtforms.validators import AnyOf, required, length

class LoginForm(Form):
    username = TextField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
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

class UserForm(Form):
    email = StringField(u'E-mail', [required(), length(max=80)])
    teamname = StringField(u'Team name', [length(max=80)], description="A name that identifies your team, if you have one")
    webpage_url = StringField(u'Team web link', [length(max=128)], description="A website, GitHub or Twitter account of your team")
    password = PasswordField(u'New password', [length(max=128)])
    submit = SubmitField(u'Save')

class ProjectForm(Form):
    event_id = SelectField(u'Event', coerce=int)
    category_id = SelectField(u'Category or challenge', coerce=int)
    AUTOTEXT__HELP = u"Enter the URL of a supported service (GitHub, Bitbucket) to populate other fields automatically."
    autotext_url = StringField(u'Autofill link', [length(max=255)], description=AUTOTEXT__HELP)
    name = StringField(u'Title', [required(), length(max=80)])
    summary = StringField(u'Short summary (120 chars)', [length(max=120)])
    longtext = TextAreaField(u'Full description (Markdown)')
    tagwords = StringField(u'Tags (separated by space)', [length(max=255)])
    webpage_url = StringField(u'Project home link', [length(max=255)])
    source_url = StringField(u'Source code link', [length(max=255)])
    image_url = StringField(u'Banner image link', [length(max=255)])
    logo_color = StringField(u'Custom color (hexadecimal)', [length(max=6)], description='A handy color picker: http://color.hailpixel.com/')
    logo_icon = StringField(u'Custom icon (Font Awesome)', [length(max=20)], description='Pick an icon here: http://fortawesome.github.io/Font-Awesome/icons/')
    submit = SubmitField(u'Save')
