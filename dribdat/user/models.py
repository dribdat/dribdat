# -*- coding: utf-8 -*-
import datetime as dt

from flask_login import UserMixin

from dribdat.extensions import bcrypt
from dribdat.database import (
    Column,
    db,
    Model,
    ReferenceCol,
    relationship,
    SurrogatePK,
)

from sqlalchemy import or_


class Role(SurrogatePK, Model):
    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = ReferenceCol('users', nullable=True)
    user = relationship('User', backref='roles')

    def __init__(self, name, **kwargs):
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Role({name})>'.format(name=self.name)


class User(UserMixin, SurrogatePK, Model):

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    teamname = Column(db.String(128), nullable=True)
    webpage_url = Column(db.String(128), nullable=True)
    password = Column(db.String(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)

    def __init__(self, username=None, email=None, password=None, **kwargs):
        if username and email:
            db.Model.__init__(self, username=username, email=email, **kwargs)
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, value):
        return bcrypt.check_password_hash(self.password, value)

    def __repr__(self):
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
    def countdown(self):
        if self.starts_at > dt.datetime.utcnow():
            return self.starts_at
        elif self.ends_at > dt.datetime.utcnow():
            return self.ends_at
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
    logo_color = Column(db.String(6), nullable=True)
    logo_icon = Column(db.String(20), nullable=True)
    longtext = Column(db.UnicodeText(), nullable=False, default=u"")
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    is_hidden = Column(db.Boolean(), default=False)

    # User who created the project
    user_id = ReferenceCol('users', nullable=True)
    user = relationship('User', backref='projects')

    # Event under which this project belongs
    event_id = ReferenceCol('events', nullable=True)
    event = relationship('Event', backref='projects')

    # And the optional event category
    category_id = ReferenceCol('categories', nullable=True)
    category = relationship('Category', backref='projects')

    def categories_all(self):
        return Category.query.order_by('name')
    def categories_global(self):
        return Category.query.filter_by(event_id=None).order_by('name')
    def categories_event(self):
        return Category.query.filter_by(event_id=self.event_id).order_by('name')

    @property
    def score(self):
        if not self.activities: return 0
        return self.activities[-1].score

    @property
    def data(self):
        return {
            'name': self.name,
            'score': self.score,
            'summary': self.summary,
            'image_url': self.image_url,
        }

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Event({name})>'.format(name=self.name)

class Category(SurrogatePK, Model):
    __tablename__ = 'categories'
    name = Column(db.String(80), nullable=False)
    description = Column(db.UnicodeText(), nullable=True)
    logo_color = Column(db.String(6), nullable=True)
    logo_icon = Column(db.String(20), nullable=True)

    # If specific to an event
    event_id = ReferenceCol('events', nullable=True)
    event = relationship('Event', backref='categories')

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
        'award',
        'star',
        name="activity_type"))
    timestamp = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    score = Column(db.Integer(), nullable=True, default=0)
    user_id = ReferenceCol('users', nullable=False)
    user = relationship('User', backref='activities')
    project_id = ReferenceCol('projects', nullable=False)
    project = relationship('Project', backref='activities')

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
