# -*- coding: utf-8 -*-
"""User models."""

from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlencode

import re
import hashlib
import datetime as dt
from time import mktime
import pytz

from flask_login import UserMixin
from flask import current_app

from dribdat.extensions import hashing
from dribdat.database import (
    db,
    Model,
    Column,
    PkModel,
    relationship,
    reference_col,
)
from dribdat.utils import (
    format_date_range, format_date, timesince
)
from dribdat.onebox import format_webembed
from dribdat.user import getProjectPhase, getResourceType

from sqlalchemy import Table, or_

users_roles = Table('users_roles', db.metadata,
    Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Role(PkModel):
    """ Loud and proud """

    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)

    def __init__(self, name=None, **kwargs):
        """Create instance."""
        super().__init__(name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"

    # Number of users
    def user_count(self):
        users = User.query.filter(User.roles.contains(self))
        return users.count()

class User(UserMixin, PkModel):
    """ Just a regular Joe """

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    webpage_url = Column(db.String(128), nullable=True)

    sso_id = Column(db.String(128), nullable=True)
    #: The hashed password
    password = Column(db.String(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    # State flags
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)

    # External profile
    cardtype = Column(db.String(80), nullable=True)
    carddata = Column(db.String(255), nullable=True)

    # Internal profile
    roles = relationship('Role', secondary=users_roles, backref='users')
    my_story = Column(db.UnicodeText(), nullable=True)
    my_goals = Column(db.UnicodeText(), nullable=True)

    @property
    def data(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'url': self.webpage_url,
            'sso': self.sso_id,
            'roles': ",".join([r.name for r in self.roles]),
            'active': self.active,
            'admin': self.is_admin,
        }

    def socialize(self):
        """ Parse the user's web profile """
        self.cardtype = ""
        if self.webpage_url is None:
            self.webpage_url = ""
        elif 'github.com/' in self.webpage_url:
            self.cardtype = 'github'
            # self.carddata = self.webpage_url.strip('/').split('/')[-1]
        elif 'twitter.com/' in self.webpage_url:
            self.cardtype = 'twitter-square'
            # self.carddata = self.webpage_url.strip('/').split('/')[-1]
        elif 'linkedin.com/' in self.webpage_url:
            self.cardtype = 'linkedin-square'
        elif 'stackoverflow.com/' in self.webpage_url:
            self.cardtype = 'stack-overflow'
        gr_size = 80
        email = self.email.lower().encode('utf-8')
        gravatar_url = hashlib.md5(email).hexdigest() + "?"
        gravatar_url += urlencode({'s':str(gr_size)})
        self.carddata = gravatar_url
        self.save()

    def joined_projects(self):
        """ Retrieve all projects user has joined """
        activities = Activity.query.filter_by(
                user_id=self.id, name='star'
            ).order_by(Activity.timestamp.desc()).all()
        projects = []
        for a in activities:
            if not a.project in projects and not a.project.is_hidden:
                projects.append(a.project)
        return projects

    def latest_posts(self, max=None):
        """ Retrieve the latest content from the user """
        activities = Activity.query.filter_by(
                user_id=self.id, action='post'
            ).order_by(Activity.timestamp.desc())
        if max is not None:
            activities = activities.limit(max)
        posts = []
        for a in activities.all():
            if not a.project.is_hidden:
                posts.append(a.data)
        return posts

    @property
    def last_active(self):
        """ Retrieve last user activity """
        act = Activity.query.filter_by(
                user_id=self.id
            ).order_by(Activity.timestamp.desc()).first()
        if not act: return 'Never'
        return act.timestamp

    @property
    def activity_count(self):
        """ Retrieve count of a user's activities """
        return Activity.query.filter_by(
                user_id=self.id
            ).count()

    def get_cert_path(self, event):
        """ Generate URL to participation certificate """
        if not event: return None
        if not event.certificate_path: return None
        path = event.certificate_path
        userdata = self.data
        for m in ['sso', 'username', 'email']:
            if m in userdata and userdata[m]:
                path = path.replace('{%s}' % m, userdata[m])
            else:
                return None
        return path

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


class Event(PkModel):
    """ Tell me what's a-happening """
    __tablename__ = 'events'
    name = Column(db.String(80), unique=True, nullable=False)
    hostname = Column(db.String(80), nullable=True)
    location = Column(db.String(255), nullable=True)
    description = Column(db.UnicodeText(), nullable=True)
    boilerplate = Column(db.UnicodeText(), nullable=True)
    resources = Column(db.UnicodeText(), nullable=True)

    logo_url = Column(db.String(255), nullable=True)
    custom_css = Column(db.UnicodeText(), nullable=True)

    webpage_url = Column(db.String(255), nullable=True)
    community_url = Column(db.String(255), nullable=True)
    community_embed = Column(db.UnicodeText(), nullable=True)
    certificate_path = Column(db.String(1024), nullable=True)

    starts_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    ends_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    is_hidden = Column(db.Boolean(), default=False)
    is_current = Column(db.Boolean(), default=False)
    lock_editing = Column(db.Boolean(), default=False)
    lock_starting = Column(db.Boolean(), default=False)
    lock_resources = Column(db.Boolean(), default=False)

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
            'has_finished': self.has_finished,
            'community_url': self.community_url,
            'webpage_url': self.webpage_url,
        }

    def get_schema(self, host_url=''):
        return {
            "@context": "http://schema.org",
            "@type":"Event",
            "location":{ "@type":"Place",
                "name": self.hostname,
                "address": self.location
            },
            "name": self.name,
            "url": host_url + self.url,
            "description": re.sub('<[^>]*>', '', self.description),
            "startDate": format_date(self.starts_at, '%Y-%m-%dT%H:%M'),
            "endDate": format_date(self.ends_at, '%Y-%m-%dT%H:%M'),
            "logo": self.logo_url,
            "mainEntityOfPage": self.webpage_url,
            "offers":{ "@type":"Offer", "url": self.webpage_url },
            "workPerformed":[ p.get_schema(host_url) for p in self.projects ]
        }

    # TODO: allow this to be configured
    @property
    def license(self):
        return "http://creativecommons.org/licenses/by/4.0/"

    @property
    def url(self):
        return "event/%d" % (self.id)
    @property
    def has_started(self):
        return self.starts_at <= dt.datetime.utcnow() <= self.ends_at
    @property
    def has_finished(self):
        return dt.datetime.utcnow() > self.ends_at
    @property
    def can_start_project(self):
        return not self.has_finished and not self.lock_starting

    @property
    def countdown(self):
        # Normalizing dates & timezones.
        tz = pytz.timezone(current_app.config['TIME_ZONE'])
        starts_at = tz.localize(self.starts_at)
        ends_at = tz.localize(self.ends_at)
        # Check event time limit (hard coded to 30 days)
        tz_now = tz.localize(dt.datetime.utcnow())
        TIME_LIMIT = tz_now + dt.timedelta(days=30)
        # Show countdown within limits
        if starts_at > tz_now:
            if starts_at > TIME_LIMIT: return None
            return starts_at
        elif ends_at > tz_now:
            if ends_at > TIME_LIMIT: return None
            return ends_at
        else:
            return None

    @property
    def date(self):
        return format_date_range(self.starts_at, self.ends_at)

    # Event categories
    def categories_for_event(self, event_id=None):
        if event_id is None: event_id = self.id
        return Category.query.filter(or_(
            Category.event_id==None,
            Category.event_id==event_id
        )).order_by('name')

    # Number of projects
    @property
    def project_count(self):
        if not self.projects: return 0
        return len(self.projects)

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Event({name})>'.format(name=self.name)

class Project(PkModel):
    """ You know, for kids! """
    __tablename__ = 'projects'
    name = Column(db.String(80), unique=True, nullable=False)
    summary = Column(db.String(120), nullable=True)
    image_url = Column(db.String(255), nullable=True)
    source_url = Column(db.String(255), nullable=True)
    webpage_url = Column(db.String(2048), nullable=True)
    is_webembed = Column(db.Boolean(), default=False)
    contact_url = Column(db.String(255), nullable=True)
    autotext_url = Column(db.String(255), nullable=True)
    is_autoupdate = Column(db.Boolean(), default=True)
    autotext = Column(db.UnicodeText(), nullable=True, default=u"")
    longtext = Column(db.UnicodeText(), nullable=False, default=u"")
    hashtag = Column(db.String(40), nullable=True)
    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(40), nullable=True)

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

    # Self-assessment and total score
    progress = Column(db.Integer(), nullable=True, default=-1)
    score = Column(db.Integer(), nullable=True, default=0)

    # Convenience query for latest activity
    def latest_activity(self, max=5):
        return Activity.query.filter_by(project_id=self.id).order_by(Activity.timestamp.desc()).limit(max)

    # Return all starring users (A team)
    def team(self):
        activities = Activity.query.filter_by(
            name='star', project_id=self.id
        ).all()
        members = []
        for a in activities:
            if not a.user in members and a.user.active:
                members.append(a.user)
        return members

    # Query which formats the project's timeline
    def all_signals(self):
        activities = Activity.query.filter_by(
                        project_id=self.id
                    ).order_by(Activity.timestamp.desc())
        signals = []
        prev = None
        for a in activities:
            title = text = None
            author = a.user.username
            if a.action == 'sync':
                title = "Synchronized"
                text = "Readme fetched from source"
            elif a.action == 'post' and a.content is not None:
                title = ""
                text = a.content
            elif a.name == 'star':
                title = "Team forming"
                text = a.user.username + " has joined!"
                author = ""
            elif a.name == 'update':
                title = ""
                text = "Worked on documentation"
            elif a.name == 'create':
                title = "Project started"
                text = "Initialized by %s &#x1F389;" % a.user.username
                author = ""
            else:
                continue
            # Check if user is still active
            if not a.user.active: continue
            # Check if last signal very similar
            if prev is not None:
                if (
                    prev['title'] == title and prev['text'] == text
                    # and (prev['date']-a.timestamp).total_seconds() < 120
                ):
                    continue
            prev = {
                'title': title,
                'text': text,
                'author': author,
                'date': a.timestamp,
                'resource': a.resource,
            }
            signals.append(prev)
        if self.event.has_started or self.event.has_finished:
            signals.append({
                'title': "Event started",
                'date': self.event.starts_at
            })
        if self.event.has_finished:
            signals.append({
                'title': "Event finished",
                'date': self.event.ends_at
            })
        return sorted(signals, key=lambda x: x['date'], reverse=True)

    # Convenience query for all categories
    def categories_all(self, event=None):
        if self.event: return self.event.categories_for_event()
        if event is not None: return event.categories_for_event()
        return Category.query.order_by('name')

    # Self-assessment (progress)
    @property
    def phase(self):
        return getProjectPhase(self)
    @property
    def is_challenge(self):
        if self.progress is None: return False
        return self.progress < 0

    @property
    def webembed(self):
        """ Detect and return supported embed widgets """
        return format_webembed(self.webpage_url)

    @property
    def longhtml(self):
        """ Process project longtext and return HTML """
        if not self.longtext or len(self.longtext) < 3:
            return self.longtext
        # TODO: apply onebox filter
        # TODO: apply markdown filter
        return self.longtext

    @property
    def url(self):
        """ Returns local server URL """
        return "project/%d" % (self.id)

    @property
    def data(self):
        d = {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'score': self.score,
            'phase': self.phase,
            'progress': self.progress,
            'summary': self.summary or '',
            'hashtag': self.hashtag or '',
            'image_url': self.image_url or '',
            'source_url': self.source_url or '',
            'webpage_url': self.webpage_url or '',
            'contact_url': self.contact_url or '',
            'logo_color': self.logo_color or '',
        }
        if self.user is not None:
            d['maintainer'] = self.user.username
        if self.event is not None:
            d['event_url'] = self.event.url
            d['event_name'] = self.event.name
        if self.category is not None:
            d['category_id'] = self.category.id
            d['category_name'] = self.category.name
        return d

    def get_schema(self, host_url=''):
        """ Schema.org compatible metadata """
        return {
            "@type": "CreativeWork",
            "name": self.name,
            "description": re.sub('<[^>]*>', '', self.summary),
            "dateCreated": format_date(self.created_at, '%Y-%m-%dT%H:%M'),
            "dateUpdated": format_date(self.updated_at, '%Y-%m-%dT%H:%M'),
            "discussionUrl": self.contact_url,
            "image": self.image_url,
            "license": self.event.license,
            "url": host_url + self.url
        }

    def update(self):
        """ Process data submission """
        # Correct fields
        if self.category_id == -1: self.category_id = None
        if self.logo_icon and self.logo_icon.startswith('fa-'):
            self.logo_icon = self.logo_icon.replace('fa-', '')
        if self.logo_color == '#000000':
            self.logo_color = ''
        # Check update status
        self.is_autoupdate = bool(self.autotext_url and self.autotext_url.strip())
        if not self.is_autoupdate: self.autotext = ''
        # Set the timestamp
        self.updated_at = dt.datetime.utcnow()
        if self.is_challenge:
            self.score = 0
        else:
            # Calculate score based on base progress
            score = self.progress or 0
            cqu = Activity.query.filter_by(project_id=self.id)
            c_s = cqu.count()
            # Get a point for every (join, update, ..) activity in the project's signals
            score = score + (1 * c_s)
            # Triple the score for every boost (upvote)
            # c_a = cqu.filter_by(name="boost").count()
            # score = score + (2 * c_a)
            # Add to the score for every complete documentation field
            if self.summary is None: self.summary = ''
            if len(self.summary) > 3: score = score + 3
            if self.image_url is None: self.image_url = ''
            if len(self.image_url) > 3: score = score + 3
            if self.source_url is None: self.source_url = ''
            if len(self.source_url) > 3: score = score + 3
            if self.webpage_url is None: self.webpage_url = ''
            if len(self.webpage_url) > 3: score = score + 3
            if self.logo_color is None: self.logo_color = ''
            if len(self.logo_color) > 3: score = score + 3
            if self.logo_icon is None: self.logo_icon = ''
            if len(self.logo_icon) > 3: score = score + 3
            if self.longtext is None: self.longtext = ''
            # Get more points based on how much content you share
            if len(self.longtext) > 3: score = score + 1
            if len(self.longtext) > 100: score = score + 4
            if len(self.longtext) > 500: score = score + 10
            # Points for external (Readme) content
            if self.autotext is not None:
                if len(self.autotext) > 3: score = score + 1
                if len(self.autotext) > 100: score = score + 4
                if len(self.autotext) > 500: score = score + 10
            self.score = score

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Project({name})>'.format(name=self.name)

class Category(PkModel):
    """ Is it a bird? Is it a plane? """
    __tablename__ = 'categories'
    name = Column(db.String(80), nullable=False)
    description = Column(db.UnicodeText(), nullable=True)
    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(20), nullable=True)

    # If specific to an event
    event_id = reference_col('events', nullable=True)
    event = relationship('Event', backref='categories')

    def project_count(self):
        if not self.projects: return 0
        return len(self.projects)

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Category({name})>'.format(name=self.name)

class Resource(PkModel):
    """ The kitchen larder """
    __tablename__ = 'resources'
    name = Column(db.String(80), unique=True, nullable=False)
    type_id = Column(db.Integer(), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    is_visible = Column(db.Boolean(), default=False)
    progress_tip = Column(db.Integer(), nullable=True)
    source_url = Column(db.String(2048), nullable=True)
    download_url = Column(db.String(2048), nullable=True)
    summary = Column(db.String(140), nullable=True)

    sync_content = Column(db.UnicodeText(), nullable=True)
    content = Column(db.UnicodeText(), nullable=True)

    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='resources')

    @property
    def of_type(self):
        return getResourceType(self)
    @property
    def since(self):
        return timesince(self.created_at)

    @property
    def icon(self):
        if self.type_id >= 300: # tool
            return 'cloud'
        elif self.type_id >= 200: # code
            return 'gear'
        elif self.type_id >= 100: # data
            return 'cube'
        else:
            return 'leaf'

    def get_comments(self, max=5):
        return Activity.query.filter_by(resource_id=self.id).order_by(Activity.id.desc()).limit(max)
    def count_mentions(self):
        return Activity.query.filter_by(resource_id=self.id).group_by(Activity.id).count()

    def sync(self):
        """ Synchronize supported resources """
        SyncResourceData(self)

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'since': self.since,
            'type': self.of_type,
            'url': self.source_url,
            # 'content': self.content,
            'summary': self.summary,
            'count': self.count_mentions()
        }

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Resource({name})>'.format(name=self.name)

class Activity(PkModel):
    """ Public, real time, conversational """
    __tablename__ = 'activities'
    name = Column(db.Enum(
        'create',
        'update',
        'star',
        name="activity_type"))
    action = Column(db.String(32), nullable=True)
        # 'external',
        # 'boost',
        # 'sync',
        # 'post',
        # ...
    timestamp = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    content = Column(db.UnicodeText, nullable=True)

    user_id = reference_col('users', nullable=False)
    user = relationship('User', backref='activities')

    project_id = reference_col('projects', nullable=False)
    project = relationship('Project', backref='activities')
    project_progress = Column(db.Integer, nullable=True)
    project_score = Column(db.Integer, nullable=True)

    resource_id = reference_col('resources', nullable=True)
    resource = relationship('Resource', backref='activities')

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'time': int(mktime(self.timestamp.timetuple())),
            'timesince': timesince(self.timestamp),
            'date': self.timestamp,
            'content': self.content or '',
            'user_name': self.user.username,
            'user_id': self.user.id,
            'project_id': self.project.id,
            'project_name': self.project.name,
            'project_score': self.project_score or 0,
            'project_phase': getProjectPhase(self.project),
            'resource_id': self.resource_id,
            'resource_type': getResourceType(self.resource),
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
