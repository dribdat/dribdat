# -*- coding: utf-8 -*-
"""User account forms."""

from flask_wtf import FlaskForm
from wtforms import (
    SubmitField,
    PasswordField,
    StringField, TextAreaField,
    SelectMultipleField,
    HiddenField,
    ValidationError
)
from wtforms.fields import (
    URLField, EmailField,
)
from wtforms.validators import (
    DataRequired, Email,
    EqualTo, Length,
)
from ..user.validators import UniqueValidator
from dribdat.utils import sanitize_input  # noqa: I005
from dribdat.utils import unpack_csvlist, pack_csvlist
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
        self.user = User.query.filter_by(username=self.username.data).first()
        if not self.user:
            self.username.errors.append('Unknown username')
            return False
        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False
        # Inactive users are allowed to log in, but not much else.
        return True

def validate_skillslist(field, maxchars=100):
    message = f"Individual skills shouldn't be empty or very long (more than {maxchars} chars), maybe, you forgot that this is a comma-separated list? Maybe, split one large skill into a few?"
    skills = unpack_csvlist(field.data)
    for s in skills:
        if len(s) > maxchars or len(s) == 0:
            field.errors = list(field.errors)
            field.errors.append(message)
            return False
    return True



common_user_related_fields = dict(
    skills = TextAreaField(
        u'My skills',
        validators=[Length(max=512)],
        description="A comma-separated list of things you have experience with."),
    wishes = TextAreaField(
        u'Skills wanted',
        validators=[Length(max=512)],
        description="A comma-separated list of skills you wished you had or would like to improve"),
    goals = TextAreaField(
        u'My goals',
        description=(
            "What would you like to get out of this experience? "
            "What ideas do you have for the programme? "
            "What activities would you like to see? "
            "(Essentially, anything that does not fit into a comma-separated list.)"
        )
    )
)


class RegisterForm(FlaskForm):
    """What the users see when they register."""

    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=25)]
    )
    email = EmailField(
        'Email',
        validators=[DataRequired(), Email(), Length(min=6, max=40)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, max=40)]
    )
    confirm = PasswordField(
        'Verify password',
        [DataRequired(), EqualTo('password', message='Passwords must match')]
    )
    webpage_url = URLField(u'Online profile')
    my_bio = TextAreaField(
        u'Bio',
        description="Tell us more about yourself: who you are, what is your background, what are you working on.")
    my_skills = common_user_related_fields["skills"]
    my_wishes = common_user_related_fields["wishes"]
    my_goals  = common_user_related_fields["goals"]

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
        if len(sane_username) == 0:
            self.username.errors.append('Please choose something different. Think what python could accept as a variable name?')
            return False

        user = User.query.filter_by(username=sane_username).first()
        if user:
            self.username.errors.append('A user with this name already exists')
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False

        if not validate_skillslist(self.my_skills):
            return False
        if not validate_skillslist(self.my_wishes):
            return False

        return True


class EmailForm(FlaskForm):
    """Just the e-mail, please."""

    email = EmailField(
        'Email',
        validators=[ DataRequired(), Email(), Length(min=6, max=40)]
    )
    submit = SubmitField(u'Continue')


class UserForm(FlaskForm):
    """What the users see when they click 'Edit profile'."""

    id = HiddenField('id')
    roles = SelectMultipleField(
        u'Roles', coerce=int,
        description="Choose one or more team roles for yourself.")
    fullname = StringField(
        u'Display name', [Length(max=200)],
        description="Your full name, if you want it shown on your profile and certificate.")
    webpage_url = URLField(
        u'Online profile', [Length(max=128)],
        description="Link to your website, GitHub or social media profile.")
    my_bio = TextAreaField(
        u'Bio',
        description="Who you are, what is your background, what are you working on.")
   
    my_skills = common_user_related_fields["skills"]
    my_wishes = common_user_related_fields["wishes"]
    my_goals  = common_user_related_fields["goals"]
    
    #username = StringField(
    #    u'Username', [Length(max=25), UniqueValidator(
    #        User, 'username'), DataRequired()],
    #    description="Nickname you would like to go by.")
    
    email = EmailField(
        u'E-mail address', [Length(max=80), DataRequired()],
        description="For a profile image, link this address at Gravatar.com")
    password = PasswordField(
        u'Change password', [Length(max=128)],
        description="Leave blank to keep your password as it is.")
    submit = SubmitField(u'Save changes')
    
    def validate(self):
        """Validate the form."""
        
        if not validate_skillslist(self.my_skills):
            return False
        if not validate_skillslist(self.my_wishes):
            return False

        return True
