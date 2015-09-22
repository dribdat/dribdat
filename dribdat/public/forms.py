# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import StringField, TextField, PasswordField, SubmitField
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
    first_name = StringField(u'First name', [length(max=30)])
    last_name = StringField(u'Last name', [length(max=30)])
    email = StringField(u'E-mail', [required(), length(max=80)])
    contact = StringField(u'Contact me at (phone, @handle,..)', [length(max=128)])
    password = PasswordField(u'New password')
    submit = SubmitField(u'Save')
