# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField, BooleanField,
    StringField, PasswordField,
    TextAreaField,
    SelectMultipleField,
    SelectField, HiddenField,
    RadioField
)
from wtforms.fields.html5 import (
    URLField, EmailField,
)
from wtforms.validators import DataRequired, AnyOf, length
from ..user.validators import UniqueValidator
from ..user import resourceTypeList, projectProgressList
from dribdat.user.models import User, Project, Resource

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
    roles = SelectMultipleField(u'Roles', coerce=int,
        description="Choose one or more team roles for yourself.")
    webpage_url = URLField(u'Online profile', [length(max=128)],
        description="Link to your website or a social media profile.")
    my_story = TextAreaField(u'My story',
        description="A brief bio and outline of the competencies you bring into the mix. The top portion of your profile.")
    my_goals = TextAreaField(u'My goals',
        description="What brings you here? Share a few words about your interests. This is the bottom portion of your profile.")
    username = StringField(u'Username', [length(max=25), UniqueValidator(User, 'username'), DataRequired()],
        description="Short and sweet.")
    email = EmailField(u'E-mail address', [length(max=80), DataRequired()],
        description="For a profile image, link to this address at Gravatar.com")
    password = PasswordField(u'Change password', [length(max=128)],
        description="Leave blank to keep your password as it is.")
    submit = SubmitField(u'Save changes')

class ProjectNew(FlaskForm):
    id = HiddenField('id')
    name = StringField(u'Title', [length(max=80), UniqueValidator(Project, 'name'), DataRequired()],
        description=u'A short team name or project title - you may change this later.')
    summary = StringField(u'Summary', [length(max=120)],
        description="The headline of your project, in up to 120 characters.")
    category_id = SelectField(u'Category', coerce=int, description=u'Select the challenge you plan to address.')
    contact_url = StringField(u'Contact link', [length(max=255)],
        description="How to best contact your team.")
    autotext_url = URLField(u'Sync', [length(max=255)],
        description="URL to external source of documentation in GitLab, GitHub, Bitbucket, etc.")
    submit = SubmitField(u'Save')

class ProjectForm(FlaskForm):
    id = HiddenField('id')
    # is_autoupdate = BooleanField(u'Sync project data')
    name = StringField(u'Title', [length(max=80), UniqueValidator(Project, 'name'), DataRequired()],
        description="[Required] a short project name, max 80 characters.")
    summary = StringField(u'Summary', [length(max=120)],
        description="Max 120 characters.")
    longtext = TextAreaField(u'Pitch',
        description="To format, use Markdown or HTML. Links on their own line get previews for supported providers.")
    webpage_url = URLField(u'Project link', [length(max=2048)],
        description="URL to a live demo, presentation, or link to further information.")
    is_webembed = BooleanField(u'Embed project link')
    autotext_url = URLField(u'Sync', [length(max=255)],
        description="URL to external source of documentation in GitLab, GitHub, Bitbucket, etc.")
    source_url = URLField(u'Source link', [length(max=255)],
        description="URL of your repository.")
    contact_url = URLField(u'Contact link', [length(max=255)],
        description="URL of an issues page, forum thread, chat channel, contact form, social media account, etc.")
    # Note: relative links allowed in image_url -> StringField
    image_url = StringField(u'Image link', [length(max=255)],
        description="URL of an image to display at the top.")
    logo_color = StringField(u'Custom color', [length(max=7)],
        description="Background color of your project page.")
    # logo_icon = StringField(u'<a target="_blank" href="http://fontawesome.io/icons/#search">Custom icon</a>',
    #     [length(max=20)], description="A FontAwesome icon for the project browser.")
    category_id = SelectField(u'Challenge category', coerce=int)
    submit = SubmitField(u'Save changes')

class ProjectPost(FlaskForm):
    id = HiddenField('id')
    note = TextAreaField(u'Note', [length(max=140), DataRequired()],
        description=u'What are you working on right now?')
    progress = SelectField(u'Progress', coerce=int)
    resource = SelectField(u'Resources', coerce=int,
        description=u'Are you using one of these?')
    submit = SubmitField(u'Save post')

class ResourceForm(FlaskForm):
    """ For suggesting cool tools """
    name = StringField(u'Name', [length(max=80), DataRequired()])
    type_id = RadioField(u'Type', coerce=int, choices=resourceTypeList())
    source_url = URLField(u'Link', [length(max=2048)],
        description=u'URL to download or get more information.')
    summary = StringField(u'Summary', [length(max=140)],
        description=u'How is this useful: in 140 characters or less?')
    content = TextAreaField(u'Additional information',
        description=u'Describe this resource in detail, Markdown and HTML supported.')
    progress_tip = SelectField(u'Recommended stage', coerce=int, choices=projectProgressList(True, True),
        description=u'Project level at which this should be suggested.')
    submit = SubmitField(u'Suggest')
