# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms.fields.html5 import URLField, EmailField

from dribdat.utils import sanitize_input

from .models import User


class RegisterForm(FlaskForm):
    """ Ye olde user registration form """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=3, max=25)])
    email = EmailField('Email',
                        validators=[DataRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Verify password',
                            [DataRequired(), EqualTo('password', message='Passwords must match')])
    webpage_url = URLField(u'Online profile')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        sane_username = sanitize_input(self.username.data)
        user = User.query.filter_by(username=sane_username).first()
        if user:
            self.username.errors.append('A user with this name already exists')
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False
        return True
