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
from dribdat.user.constants import (
    PR_CHALLENGE,
    getProjectPhase,
    getResourceType,
    getStageByProgress,
)

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

    def joined_projects(self, with_challenges=True):
        """ Retrieve all projects user has joined """
        activities = Activity.query.filter_by(
                user_id=self.id, name='star'
            ).order_by(Activity.timestamp.desc()).all()
        projects = []
        for a in activities:
            if not a.project in projects and not a.project.is_hidden:
                if with_challenges or a.project.progress != 0:
                    projects.append(a.project)
        return projects

    def posted_challenges(self):
        """ Retrieve all challenges user has posted """
        projects = Project.query.filter_by(
                user_id=self.id, progress=0, is_hidden=False
            ).order_by(Project.id.desc()).all()
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
    summary = Column(db.String(140), nullable=True)
    description = Column(db.UnicodeText(), nullable=True)
    boilerplate = Column(db.UnicodeText(), nullable=True)
    instruction = Column(db.UnicodeText(), nullable=True)

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
            "description": self.summary or re.sub('<[^>]*>', '', self.description),
            "startDate": format_date(self.starts_at, '%Y-%m-%dT%H:%M'),
            "endDate": format_date(self.ends_at, '%Y-%m-%dT%H:%M'),
            "logo": self.logo_url,
            "mainEntityOfPage": self.webpage_url,
            "offers":{ "@type":"Offer", "url": self.webpage_url },
            "workPerformed":[ p.get_schema(host_url) for p in self.projects ]
        }

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
    def ends_at_tz(self):
        tz = pytz.timezone(current_app.config['TIME_ZONE'])
        return tz.localize(self.ends_at)
    @property
    def starts_at_tz(self):
        tz = pytz.timezone(current_app.config['TIME_ZONE'])
        return tz.localize(self.starts_at)
    @property
    def countdown(self):
        """ Normalized countdown timer """
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
        """ Formatted date range """
        return format_date_range(self.starts_at, self.ends_at)
    @property
    def oneliner(self):
        """ A short online description """
        ol = self.summary or self.description
        ol = re.sub(r"\s+", " ", ol)
        if len(ol)>140: ol = ol[:140] + '...'
        return ol
    @property
    def project_count(self):
        """ Number of projects """
        if not self.projects: return 0
        return len(self.projects)

    def categories_for_event(self):
        """ Event categories """
        return Category.query.filter(or_(
            Category.event_id==None,
            Category.event_id==-1,
            Category.event_id==self.id
        )).order_by('name')

    def current():
        """ Returns currently featured event """
        # TODO: allow multiple featurettes?
        return Event.query.filter_by(is_current=True).first()

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Event({name})>'.format(name=self.name)

class Project(PkModel):
    """ You know, for kids! """
    __tablename__ = 'projects'
    name = Column(db.String(80), unique=True, nullable=False)
    summary = Column(db.String(140), nullable=True)
    hashtag = Column(db.String(40), nullable=True)

    image_url = Column(db.String(2048), nullable=True)
    source_url = Column(db.String(2048), nullable=True)
    webpage_url = Column(db.String(2048), nullable=True)
    contact_url = Column(db.String(2048), nullable=True)
    autotext_url = Column(db.String(2048), nullable=True)
    download_url = Column(db.String(2048), nullable=True)

    is_hidden = Column(db.Boolean(), default=False)
    is_webembed = Column(db.Boolean(), default=False)
    is_autoupdate = Column(db.Boolean(), default=True)

    autotext = Column(db.UnicodeText(), nullable=True, default=u"")
    longtext = Column(db.UnicodeText(), nullable=False, default=u"")

    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(40), nullable=True)

    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

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

    def latest_activity(self, max=5):
        """ Convenience query for latest activity """
        return Activity.query.filter_by(project_id=self.id).order_by(Activity.timestamp.desc()).limit(max)

    def team(self):
        """ Return all starring users (A team) """
        activities = Activity.query.filter_by(
            name='star', project_id=self.id
        ).all()
        members = []
        for a in activities:
            if not a.user in members and a.user.active:
                members.append(a.user)
        return members

    def all_dribs(self):
        """ Query which formats the project's timeline """
        activities = Activity.query.filter_by(
                        project_id=self.id
                    ).order_by(Activity.timestamp.desc())
        dribs = []
        prev = None
        for a in activities:
            author = title = text = None
            if a.user:
                author = a.user.username
                if not a.user.active: continue
            if a.action == 'sync':
                title = "Synchronized"
                text = "Readme fetched from source"
                continue
            elif a.action == 'post' and a.content is not None:
                title = ""
                text = a.content
            elif a.name == 'star':
                title = "Team forming"
                text = a.user.username + " has joined!"
                author = ""
            elif a.name == 'update' and a.action == 'commit':
                title = "Code commit"
                text = a.content
                author = None #a.user.username
            elif a.name == 'update':
                title = ""
                text = "Worked on documentation"
            elif a.name == 'create':
                title = "Project started"
                text = "Initialized by %s &#x1F389;" % a.user.username
                author = ""
            else:
                continue
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
                # 'resource': a.resource,
                'ref_url': a.ref_url,
            }
            dribs.append(prev)
        if self.event.has_started or self.event.has_finished:
            dribs.append({
                'title': "Event started",
                'date': self.event.starts_at
            })
        if self.event.has_finished:
            dribs.append({
                'title': "Event finished",
                'date': self.event.ends_at
            })
        return sorted(dribs, key=lambda x: x['date'], reverse=True)

    def categories_all(self, event=None):
        """ Convenience query for all categories """
        if self.event: return self.event.categories_for_event()
        if event is not None: return event.categories_for_event()
        return Category.query.order_by('name')

    @property
    def stage(self):
        """ Assessment of progress stage with full data """
        return getStageByProgress(self.progress)
    @property
    def phase(self):
        """ Assessment of progress as phase name """
        return getProjectPhase(self)
    @property
    def is_challenge(self):
        """ True if this project is in challenge phase """
        if self.progress is None: return False
        return self.progress <= PR_CHALLENGE

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
            'excerpt': '',
        }
        d['team'] = [ u.username for u in self.team() ]
        if len(self.longtext) > 10:
            d['excerpt'] = self.longtext[:300] + '...'
        elif self.is_autoupdate:
            d['excerpt'] = self.autotext[:300] + '...'
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
        # TODO: accurately detect project license based on component etc.
        content_license = "https://creativecommons.org/licenses/by/4.0/" if "creativecommons" in self.event.community_embed else ''
        return {
            "@type": "CreativeWork",
            "name": self.name,
            "description": re.sub('<[^>]*>', '', self.summary),
            "dateCreated": format_date(self.created_at, '%Y-%m-%dT%H:%M'),
            "dateUpdated": format_date(self.updated_at, '%Y-%m-%dT%H:%M'),
            "discussionUrl": self.contact_url,
            "image": self.image_url,
            "license": content_license,
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
            # Get a point for every (join, update, ..) activity in the project's dribs
            score = score + (1 * c_s)
            # Triple the score for every boost (upvote)
            # c_a = cqu.filter_by(name="boost").count()
            # score = score + (2 * c_a)
            # Add to the score for every complete documentation field
            if self.summary is None: self.summary = ''
            if len(self.summary) > 3: score = score + 1
            if self.image_url is None: self.image_url = ''
            if len(self.image_url) > 3: score = score + 1
            if self.source_url is None: self.source_url = ''
            if len(self.source_url) > 3: score = score + 1
            if self.webpage_url is None: self.webpage_url = ''
            if len(self.webpage_url) > 3: score = score + 1
            if self.logo_color is None: self.logo_color = ''
            if len(self.logo_color) > 3: score = score + 1
            if self.logo_icon is None: self.logo_icon = ''
            if len(self.logo_icon) > 3: score = score + 1
            if self.longtext is None: self.longtext = ''
            # Get more points based on how much content you share
            if len(self.longtext) > 3: score = score + 1
            if len(self.longtext) > 100: score = score + 3
            if len(self.longtext) > 500: score = score + 5
            # Points for external (Readme) content
            if self.autotext is not None:
                if len(self.autotext) > 3: score = score + 1
                if len(self.autotext) > 100: score = score + 3
                if len(self.autotext) > 500: score = score + 5
            # Cap at 100%
            if score > 100: score = 100
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
            # 'event_id': self.event_id,
        }

    def __init__(self, name=None, **kwargs):
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Category({name})>'.format(name=self.name)

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
        # 'commit',
        # 'boost',
        # 'sync',
        # 'post',
        # ...
    timestamp = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    content = Column(db.UnicodeText, nullable=True)
    ref_url = Column(db.String(2048), nullable=True)

    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='activities')

    # resource_id = reference_col('resources', nullable=True)
    # resource = relationship('Resource', backref='activities')

    project_id = reference_col('projects', nullable=True)
    project = relationship('Project', backref='activities')
    project_progress = Column(db.Integer, nullable=True)
    project_score = Column(db.Integer, nullable=True)

    @property
    def data(self):
        a = {
            'id': self.id,
            'name': self.name,
            'time': int(mktime(self.timestamp.timetuple())),
            'timesince': timesince(self.timestamp),
            'date': self.timestamp,
            'content': self.content or '',
            'ref_url': self.ref_url or '',
        }
        if self.user:
            a['user_id'] = self.user.id
            a['user_name'] = self.user.username
        if self.project:
            a['project_id'] = self.project.id
            a['project_name'] = self.project.name
            a['project_score'] = self.project_score or 0
            a['project_phase'] = getProjectPhase(self.project)
        return a

    def __init__(self, name, project_id, **kwargs):
        if name:
            db.Model.__init__(
                self, name=name,
                project_id=project_id,
                **kwargs
            )

    def __repr__(self):
        return '<Activity({name})>'.format(name=self.name)


class Resource(PkModel):
    """ Somewhat graph-like in principle """
    __tablename__ = 'resources'
    name = Column(db.String(80), nullable=False)
    type_id = Column(db.Integer(), nullable=True, default=0)

    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    # At which progress level did it become relevant
    progress_tip = Column(db.Integer(), nullable=True)
    # order = Column(db.Integer, nullable=True)
    source_url = Column(db.String(2048), nullable=True)
    is_visible = Column(db.Boolean(), default=True)

    # This is the text content of a comment or description
    content = Column(db.UnicodeText, nullable=True)
    # JSON blob of externally fetched structured content
    sync_content = Column(db.UnicodeText, nullable=True)

    # The project this is referenced in
    project_id = reference_col('projects', nullable=True)
    project = relationship('Project', backref='components')

    @property
    def of_type(self):
        return getResourceType(self)

    @property
    def data(self):
        return {
            'id': self.id,
            'date': self.created_at,
            'name': self.name,
            'of_type': self.type_id,
            'url': self.source_url or '',
            'content': self.content or '',
            'project_id': self.project_id,
            # 'project_name': self.project.name
        }

    def __init__(self, name, project_id, **kwargs):
        db.Model.__init__(
            self, name=name, project_id=project_id,
            **kwargs
        )

    def __repr__(self):
        return '<Resource({name})>'.format(name=self.name)
