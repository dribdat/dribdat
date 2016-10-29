# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt
import urllib, hashlib
from time import mktime

from flask_login import UserMixin

from dribdat.extensions import hashing
from dribdat.database import (
    Column,
    db,
    Model,
    reference_col,
    relationship,
    SurrogatePK,
)

from dribdat.user import PROJECT_PROGRESS_PHASE

from sqlalchemy import or_

class Role(SurrogatePK, Model):
    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='roles')

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Role({name})>'.format(name=self.name)


class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    webpage_url = Column(db.String(128), nullable=True)
    #: The hashed password
    password = Column(db.String(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)

    cardtype = Column(db.String(80), nullable=True)
    carddata = Column(db.String(255), nullable=True)

    @property
    def data(self):
        return {
            'id': self.id,
            'username': self.username,
        }

    def socialize(self):
        if 'github.com/' in self.webpage_url:
            self.cardtype = 'github'
            self.carddata = self.webpage_url.strip('/').split('/')[-1]
        elif 'twitter.com/' in self.webpage_url:
            self.cardtype = 'twitter'
            self.carddata = self.webpage_url.strip('/').split('/')[-1]
        else:
            gr_size = 40
            gravatar_url = hashlib.md5(self.email.lower()).hexdigest() + "?"
            gravatar_url += urllib.urlencode({'s':str(gr_size)})
            self.cardtype = 'gravatar'
            self.carddata = gravatar_url
        self.save()

    def __init__(self, username=None, email=None, password=None, **kwargs):
        """Create instance."""
        if username and email:
            db.Model.__init__(self, username=username, email=email, **kwargs)
        if password:
            self.set_password(password)

    def set_password(self, password):
        """Set password."""
        self.password = hashing.hash_value(password)

    def check_password(self, value):
        """Check password."""
        return hashing.check_value(self.password, value)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r})>'.format(username=self.username)


class Event(SurrogatePK, Model):
    __tablename__ = 'events'
    name = Column(db.String(80), unique=True, nullable=False)
    hostname = Column(db.String(80), nullable=True)
    location = Column(db.String(255), nullable=True)
    description = Column(db.UnicodeText(), nullable=True)

    logo_url = Column(db.String(255), nullable=True)
    custom_css = Column(db.UnicodeText(), nullable=True)

    webpage_url = Column(db.String(255), nullable=True)
    community_url = Column(db.String(255), nullable=True)
    community_embed = Column(db.UnicodeText(), nullable=True)

    starts_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    ends_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    is_current = Column(db.Boolean(), default=False)

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'location': self.location,
            'starts_at': self.starts_at,
            'has_started': self.has_started,
            'ends_at': self.ends_at,
            'info_url': self.webpage_url,
        }

    @property
    def has_started(self):
        return self.starts_at <= dt.datetime.utcnow() <= self.ends_at

    @property
    def countdown(self):
        if self.starts_at > dt.datetime.utcnow():
            return self.starts_at + dt.timedelta(hours=2) # TODO: timezones...
        elif self.ends_at > dt.datetime.utcnow():
            return self.ends_at + dt.timedelta(hours=2)
        else:
            return None

    @property
    def date(self):
        if self.starts_at.month == self.ends_at.month:
            return "{0} {1}-{2}, {3}".format(
                self.starts_at.strftime("%B"),
                self.starts_at.day,
                self.ends_at.day,
                self.ends_at.year,
            )
        else:
            return "{0} {1}, {2} - {3} {4}, {5}".format(
                self.starts_at.strftime("%B"),
                self.starts_at.day,
                self.starts_at.year,
                self.ends_at.strftime("%B"),
                self.ends_at.day,
                self.ends_at.year,
            )

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Event({name})>'.format(name=self.name)

class Project(SurrogatePK, Model):
    __tablename__ = 'projects'
    name = Column(db.String(80), unique=True, nullable=False)
    summary = Column(db.String(120), nullable=True)
    image_url = Column(db.String(255), nullable=True)
    source_url = Column(db.String(255), nullable=True)
    webpage_url = Column(db.String(255), nullable=True)
    autotext_url = Column(db.String(255), nullable=True)
    is_autoupdate = Column(db.Boolean(), default=True)
    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(40), nullable=True)
    hashtag = Column(db.String(40), nullable=True)
    longtext = Column(db.UnicodeText(), nullable=False, default=u"")
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    is_hidden = Column(db.Boolean(), default=False)

    # User who created the project
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='projects')

    # Event under which this project belongs
    event_id = reference_col('events', nullable=True)
    event = relationship('Event', backref='projects')

    # And the optional event category
    category_id = reference_col('categories', nullable=True)
    category = relationship('Category', backref='projects')

    def categories_all(self):
        return Category.query.order_by('name')
    def categories_global(self):
        return Category.query.filter_by(event_id=None).order_by('name')
    def categories_event(self):
        return Category.query.filter_by(event_id=self.event_id).order_by('name')

    # Self-assessment
    progress = Column(db.Integer(), nullable=True, default=0)
    @property
    def phase(self):
        if self.progress is None: return ""
        return PROJECT_PROGRESS_PHASE[self.progress]

    # Current tally
    score = Column(db.Integer(), nullable=True, default=0)

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'score': self.score,
            'phase': self.phase,
            'summary': self.summary,
            'hashtag': self.hashtag,
            'image_url': self.image_url,
        }

    def update(self):
        # Calculate score based on base progress
        score = self.progress or 0
        cqu = Activity.query.filter_by(project_id=self.id)
        c_s = cqu.filter_by(name="star").count()
        score = score + (2 * c_s)
        # c_a = cqu.filter_by(name="boost").count()
        # score = score + (10 * c_a)
        if self.summary is None: self.summary = ''
        if len(self.summary) > 3: score = score + 3
        if self.image_url is None: self.image_url = ''
        if len(self.image_url) > 3: score = score + 3
        if self.source_url is None: self.source_url = ''
        if len(self.source_url) > 3: score = score + 10
        if self.webpage_url is None: self.webpage_url = ''
        if len(self.webpage_url) > 3: score = score + 10
        if self.logo_color is None: self.logo_color = ''
        if len(self.logo_color) > 3: score = score + 1
        if self.logo_icon is None: self.logo_icon = ''
        if len(self.logo_icon) > 3: score = score + 1
        if self.longtext is None: self.longtext = ''
        if len(self.longtext) > 3: score = score + 1
        if len(self.longtext) > 100: score = score + 4
        if len(self.longtext) > 500: score = score + 10
        self.score = score
        # Correct fields
        if self.category_id == -1: self.category_id = None
        if self.logo_icon.startswith('fa-'):
            self.logo_icon = self.logo_icon.replace('fa-', '')
        if self.logo_color == '#000000':
            self.logo_color = ''
        # Set the timestamp
        self.updated_at = dt.datetime.utcnow()

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Event({name})>'.format(name=self.name)

class Category(SurrogatePK, Model):
    __tablename__ = 'categories'
    name = Column(db.String(80), nullable=False)
    description = Column(db.UnicodeText(), nullable=True)
    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(20), nullable=True)

    # If specific to an event
    event_id = reference_col('events', nullable=True)
    event = relationship('Event', backref='categories')

    @property
    def project_count(self):
        if not self.projects: return 0
        return len(self.projects)

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Category({name})>'.format(name=self.name)

class Activity(SurrogatePK, Model):
    __tablename__ = 'activities'
    name = Column(db.Enum(
        'create',
        'update',
        # 'boost',
        'star',
        name="activity_type"))
    timestamp = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    user_id = reference_col('users', nullable=False)
    user = relationship('User', backref='activities')
    project_id = reference_col('projects', nullable=False)
    project = relationship('Project', backref='activities')

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'time': int(mktime(self.timestamp.timetuple())),
            'date': self.timestamp,
            'user': self.user.data,
            'project_id': self.project.id,
            'project_name': self.project.name,
        }

    def __init__(self, name, user_id, project_id, **kwargs):
        if name:
            db.Model.__init__(
                self, name=name,
                user_id=user_id,
                project_id=project_id,
                **kwargs
            )

    def __repr__(self):
        return '<Activity({name})>'.format(name=self.name)
