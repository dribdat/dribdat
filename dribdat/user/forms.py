# -*- coding: utf-8 -*-
"""User account forms."""

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    SubmitField,
    PasswordField,
    StringField,
    TextAreaField,
    SelectMultipleField,
    HiddenField,
)
from wtforms.fields import (
    URLField,
    EmailField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
)
from sqlalchemy import func
from ..user.validators import UniqueValidator
from dribdat.utils import sanitize_input  # noqa: I005
from .models import User


common_user_related_fields = dict(
    fullname=StringField(
        "Display name",
        [Length(max=200)],
        description="Your full name, if you want it shown on your profile and certificate.",
    ),
    webpage_url=URLField(
        "Online profile",
        [Length(max=128)],
        description="Link to your website or a social media profile.",
    ),
    username=StringField(
        "Username",
        [Length(max=40), UniqueValidator(User, "username"), DataRequired()],
        description="Short and sweet.",
    ),
    email=EmailField(
        "E-mail address",
        [Length(max=80), DataRequired()],
        description="For a profile image, link this address at Gravatar.com",
    ),
    goals=StringField(
        "My goal",
        description=(
            "What would you like to get out of this experience? "
            "What ideas or activities do you have for the program? "
            "A few words about your interests."
        ),
    ),
    skills=StringField(
        "🦾 my, skills",
        validators=[Length(max=512)],
        description="A comma-separated list of things you have experience with.",
    ),
    wishes=StringField(
        "🎋 my, aims",
        validators=[Length(max=512)],
        description="A comma-separated list of skills you wished you had, or would like to improve.",
    ),
)


class RegisterForm(FlaskForm):
    """Ye olde user registration form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=40)]
    )
    email = EmailField(
        "Email", validators=[DataRequired(), Email(), Length(min=6, max=80)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=100)]
    )
    confirm = PasswordField(
        "Verify password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    webpage_url = URLField("Online profile")
    recaptcha = RecaptchaField()
    submit = SubmitField("Continue")

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):  # pyright: ignore
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        sane_username = sanitize_input(self.username.data)
        user = User.query.filter_by(username=sane_username).first()
        if user:
            self.username.errors.append("A user with this name already exists")  # pyright: ignore
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")  # pyright: ignore
            return False
        return True


class LoginForm(FlaskForm):
    """Display a login form."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("Continue")

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):  # pyright: ignore
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False
        # Allow login with e-mail address
        if "@" in str(self.username.data):
            self.user = User.query.filter_by(email=self.username.data).first()
        else:
            self.user = User.query.filter(
                func.lower(User.username) == func.lower(self.username.data)
            ).first()
        if not self.user:
            self.username.errors.append("Could not find your user account")  # pyright: ignore
            return False
        if not self.user.check_password(self.password.data):
            self.password.errors.append("Invalid password")  # pyright: ignore
            return False
        # Inactive users are allowed to log in, but not much else.
        return True


class EmailForm(FlaskForm):
    """Just the e-mail, please."""

    username = EmailField(
        "Email", validators=[DataRequired(), Email(), Length(min=6, max=80)]
    )
    recaptcha = RecaptchaField()
    submit = SubmitField("Continue")


class ActivationForm(FlaskForm):
    """Enter the secret code here."""

    code = StringField(
        validators=[DataRequired()],
        description="Activation code from your e-mail",
    )
    recaptcha = RecaptchaField()
    submit = SubmitField("Continue")


class UserForm(FlaskForm):
    """User profile form."""

    id = HiddenField("id")

    fullname = common_user_related_fields["fullname"]
    webpage_url = common_user_related_fields["webpage_url"]
    username = common_user_related_fields["username"]
    email = common_user_related_fields["email"]

    password = PasswordField(
        "Change password",
        [Length(max=128)],
        description="Leave blank to keep your password as it is.",
    )
    submit = SubmitField("Save profile")


class StoryForm(FlaskForm):
    """User story form."""

    id = HiddenField("id")
    roles = SelectMultipleField(
        "Roles", coerce=int, description="Choose one or more team roles for yourself."
    )
    my_story = TextAreaField(
        "Biography",
        description="A brief summary of the competencies you bring "
        + "into the team. The center of your profile.",
    )
    vitae = TextAreaField("{ JSON resume }")  # Tips are shown in the footer

    my_skills = common_user_related_fields["skills"]
    my_wishes = common_user_related_fields["wishes"]
    my_goals = common_user_related_fields["goals"]

    submit = SubmitField("Save changes")
