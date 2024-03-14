# -*- coding: utf-8 -*-
"""User account forms."""

from flask_wtf import FlaskForm
from wtforms import (
    SubmitField,
    PasswordField,
    StringField, TextAreaField,
    SelectMultipleField,
    HiddenField,
)
from wtforms.fields import (
    URLField, EmailField,
)
from wtforms.validators import (
    DataRequired, Email,
    EqualTo, Length,
)
from sqlalchemy import func
from ..user.validators import UniqueValidator
from dribdat.utils import sanitize_input  # noqa: I005
from .models import User

class LoginForm(FlaskForm):
    """Display a login form."""

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
        # Allow login with e-mail address
        if '@' in self.username.data:
            self.user = User.query.filter_by(email=self.username.data).first()
        else:
            self.user = User.query.filter( \
                    func.lower(User.username) == func.lower(self.username.data) \
                ).first()
        if not self.user:
            self.username.errors.append('Could not find your user account')
            return False
        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False
        # Inactive users are allowed to log in, but not much else.
        return True


class RegisterForm(FlaskForm):
    """Ye olde user registration form."""

    username = StringField('Username',
                           validators=[DataRequired(), Length(min=3, max=25)])
    email = EmailField('Email',
                       validators=[
                          DataRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password',
                             validators=[
                                DataRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Verify password',
                            [DataRequired(), EqualTo(
                                'password',
                                message='Passwords must match')])
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


class EmailForm(FlaskForm):
    """Just the e-mail, please."""

    email = EmailField('Email',
                       validators=[
                            DataRequired(), Email(), Length(min=6, max=40)])
    submit = SubmitField(u'Continue')


class UserForm(FlaskForm):
    """User profile form."""

    id = HiddenField('id')
    roles = SelectMultipleField(
        u'Roles', coerce=int,
        description="Choose one or more team roles for yourself.")
    fullname = StringField(
        u'Display name', [Length(max=200)],
        description="Your full name, if you want it shown on your profile and certificate.")
    webpage_url = URLField(
        u'Online profile', [Length(max=128)],
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
        u'Username', [Length(max=25), UniqueValidator(
            User, 'username'), DataRequired()],
        description="Short and sweet.")
    email = EmailField(
        u'E-mail address', [Length(max=80), DataRequired()],
        description="For a profile image, link this address at Gravatar.com")
    password = PasswordField(
        u'Change password', [Length(max=128)],
        description="Leave blank to keep your password as it is.")
    submit = SubmitField(u'Save changes')
