# -*- coding: utf-8 -*-
"""User models."""

from sqlalchemy import Table, or_
from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import FlaskPlugin
from dribdat.user.constants import (
    MAX_EXCERPT_LENGTH,
    PR_CHALLENGE,
    getProjectPhase,
    getResourceType,
    getStageByProgress,
    getActivityByType,
)
from dribdat.onebox import format_webembed  # noqa: I005
from dribdat.utils import (
    format_date_range, format_date, timesince
)
from dribdat.database import (
    db,
    Column,
    PkModel,
    relationship,
    reference_col,
)
from dribdat.extensions import hashing
from dribdat.apifetch import FetchGitlabAvatar
from flask import current_app
from flask_login import UserMixin
from time import mktime
from dateutil.parser import parse
from dateutil.parser._parser import ParserError
import datetime as dt
import hashlib
import re
from urllib.parse import urlencode, urlparse
# Standard library fix
from future.standard_library import install_aliases
install_aliases()  # noqa: I005


# Set up user roles mapping
users_roles = Table(
    'users_roles', db.metadata,
    Column('user_id', db.Integer, db.ForeignKey(
        'users.id'), primary_key=True),
    Column('role_id', db.Integer, db.ForeignKey(
        'roles.id'), primary_key=True)
)


# Init SQLAlchemy Continuum
make_versioned(plugins=[FlaskPlugin()])


class Role(PkModel):
    """Loud and proud."""

    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)

    def __init__(self, name=None, **kwargs):
        """Create instance."""
        super().__init__(name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"

    def user_count(self):
        """Return the number of users in this role."""
        users = User.query.filter(User.roles.contains(self))
        return users.count()


class User(UserMixin, PkModel):
    """Just a regular Joe."""

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    webpage_url = Column(db.String(128), nullable=True)

    # Identification for Single Sign On
    sso_id = Column(db.String(128), nullable=True)
    # A temporary hash for logins
    hashword = Column(db.String(128), nullable=True)
    updated_at = Column(db.DateTime, nullable=True,
                        default=dt.datetime.utcnow)
    # The hashed password
    password = Column(db.String(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False,
                        default=dt.datetime.utcnow)

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
        """Get JSON representation."""
        return {
            'id': self.id,
            'email': self.email,
            'sso_id': self.sso_id,
            'active': self.active,
            'is_admin': self.is_admin,
            'username': self.username,
            'webpage_url': self.webpage_url,
            'roles': ",".join([r.name for r in self.roles]),
            'cardtype': self.cardtype,
            'carddata': self.carddata,
            'my_story': self.my_story,
            'my_goals': self.my_goals,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def set_from_data(self, data):
        """Update from JSON representation."""
        self.active = False  # login disabled on imported user
        self.username = data['username']
        self.webpage_url = data['webpage_url']
        if 'email' not in data:
            data['email'] = "%s@%d.localdomain" % (self.username, data['id'])
        self.email = data['email']
        self.updated_at = dt.datetime.utcnow()

    def socialize(self):
        """Parse the user's web profile."""
        self.cardtype = ""
        self.carddata = ""
        if self.webpage_url is None:
            self.webpage_url = ""
        host = urlparse(self.webpage_url).hostname
        if host == 'github.com':
            self.cardtype = 'github'
            username = self.webpage_url.strip('/').split('/')[-1]
            self.carddata = "https://github.com/%s.png?size=80" % username
        elif host == 'gitlab.com':
            self.cardtype = 'gitlab'
            self.carddata = FetchGitlabAvatar(self.email)
        elif host == 'twitter.com':
            self.cardtype = 'twitter-square'
            # username = self.webpage_url.strip('/').split('/')[-1]
            # self.carddata = FetchTwitterAvatar(username)
        elif host == 'linkedin.com':
            self.cardtype = 'linkedin-square'
        elif host and host.endswith('stackoverflow.com'):
            self.cardtype = 'stack-overflow'
        if not self.carddata:
            # Default: generate a Gravatar link
            gr_size = 80
            email = self.email.lower().encode('utf-8')
            gravatar_url = "https://www.gravatar.com/avatar/"
            gravatar_url += hashlib.md5(email).hexdigest() + "?"
            gravatar_url += urlencode({'s': str(gr_size)})
            self.carddata = gravatar_url
        self.save()

    def joined_projects(self, with_challenges=True, limit=-1):
        """Retrieve all projects user has joined."""
        activities = Activity.query.filter_by(
                user_id=self.id, name='star'
            ).order_by(Activity.timestamp.desc())
        if limit < 0:
            activities = activities.all()
        else:
            activities = activities.limit(limit)
        projects = []
        for a in activities:
            if a.project not in projects and not a.project.is_hidden:
                if with_challenges or a.project.progress != 0:
                    projects.append(a.project)
        return projects

    def posted_challenges(self):
        """Retrieve all challenges user has posted."""
        projects = Project.query.filter_by(
                user_id=self.id, progress=0, is_hidden=False
            ).order_by(Project.id.desc()).all()
        return projects

    def latest_posts(self, max=None):
        """Retrieve the latest content from the user."""
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
        """Retrieve last user activity."""
        act = Activity.query.filter_by(
                user_id=self.id
            ).order_by(Activity.timestamp.desc()).first()
        if not act:
            return 'Never'
        return act.timestamp

    @property
    def activity_count(self):
        """Retrieve count of a user's activities."""
        return Activity.query.filter_by(
                user_id=self.id
            ).count()

    def may_certify(self):
        """Check availability of certificate."""
        projects = self.joined_projects(False)
        if not len(projects) > 0:
            return (False, 'projects')
        cert_path = self.get_cert_path(projects[0].event)
        if not cert_path:
            return (False, 'event')
        return (True, cert_path)

    def get_cert_path(self, event):
        """Generate URL to participation certificate."""
        if not event:
            return None
        if not event.certificate_path:
            return None
        path = event.certificate_path
        userdata = self.data
        for m in ['sso', 'username', 'email']:
            if m in userdata and userdata[m]:
                path = path.replace('{%s}' % m, userdata[m])
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
        self.updated_at = dt.datetime.utcnow()

    def check_password(self, value):
        """Check password."""
        return hashing.check_value(self.password, value)

    def set_hashword(self, hashword):
        """Set a hash."""
        self.hashword = hashing.hash_value(hashword)
        self.updated_at = dt.datetime.utcnow()

    def check_hashword(self, value):
        """Check the hash value."""
        timediff = dt.datetime.utcnow() - self.updated_at
        if timediff > dt.timedelta(minutes=5):
            # Time limit exceeded
            return False
        return hashing.check_value(self.hashword, value)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r})>'.format(username=self.username)


class Event(PkModel):
    """Tell me what is a-happening here."""

    __tablename__ = 'events'
    name = Column(db.String(80), unique=True, nullable=False)
    summary = Column(db.String(140), nullable=True)
    hostname = Column(db.String(80), nullable=True)
    location = Column(db.String(255), nullable=True)
    hashtags = Column(db.String(255), nullable=True)

    description = Column(db.UnicodeText(), nullable=True)
    boilerplate = Column(db.UnicodeText(), nullable=True)
    instruction = Column(db.UnicodeText(), nullable=True)

    logo_url = Column(db.String(255), nullable=True)
    webpage_url = Column(db.String(255), nullable=True)
    gallery_url = Column(db.String(2048), nullable=True)
    community_url = Column(db.String(255), nullable=True)

    starts_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    ends_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    custom_css = Column(db.UnicodeText(), nullable=True)
    community_embed = Column(db.UnicodeText(), nullable=True)
    certificate_path = Column(db.String(1024), nullable=True)

    is_hidden = Column(db.Boolean(), default=False)
    is_current = Column(db.Boolean(), default=False)
    lock_editing = Column(db.Boolean(), default=False)
    lock_starting = Column(db.Boolean(), default=False)
    lock_resources = Column(db.Boolean(), default=False)

    @property
    def data(self):
        """Get JSON representation."""
        return {
            'id': self.id,
            'name': self.name,
            'summary': self.summary or '',
            'hostname': self.hostname or '',
            'location': self.location or '',
            'hashtags': self.hashtags or '',
            'starts_at': self.starts_at,
            'has_started': self.has_started,
            'ends_at': self.ends_at,
            'has_finished': self.has_finished,
            'community_url': self.community_url or '',
            'gallery_url': self.gallery_url or '',
            'webpage_url': self.webpage_url or '',
            'logo_url': self.logo_url or '',
        }

    def get_full_data(self):
        """Return full JSON event content."""
        d = self.data
        d['starts_at'] = format_date(self.starts_at, '%Y-%m-%dT%H:%M')
        d['ends_at'] = format_date(self.ends_at, '%Y-%m-%dT%H:%M')
        d['description'] = self.description or ''
        d['boilerplate'] = self.boilerplate or ''
        d['instruction'] = self.instruction or ''
        # And by full, we mean really full!
        d['custom_css'] = self.custom_css or ''
        d['community_embed'] = self.community_embed or ''
        d['certificate_path'] = self.certificate_path or ''
        return d

    def set_from_data(self, d):
        """Set from a full JSON event content."""
        self.name = d['name']
        self.summary = d['summary'] or ''
        self.ends_at = parse(d['ends_at'])
        self.starts_at = parse(d['starts_at'])
        self.hostname = d['hostname'] or '' if 'hostname' in d else ''
        self.location = d['location'] or '' if 'location' in d else ''
        self.hashtags = d['hashtags'] or '' if 'hashtags' in d else ''
        self.logo_url = d['logo_url'] or '' if 'logo_url' in d else ''
        self.custom_css = d['custom_css'] or '' if 'custom_css' in d else ''
        self.description = d['description'] or '' if 'description' in d else ''
        self.boilerplate = d['boilerplate'] or '' if 'boilerplate' in d else ''
        self.instruction = d['instruction'] or '' if 'instruction' in d else ''
        self.gallery_url = d['gallery_url'] or '' if 'gallery_url' in d else ''
        self.webpage_url = d['webpage_url'] or '' if 'webpage_url' in d else ''
        dcu = d['community_url'] or '' if 'community_url' in d else ''
        self.community_url = dcu
        dce = d['community_embed'] or '' if 'community_embed' in d else ''
        self.community_embed = dce
        dcp = d['certificate_path'] or '' if 'certificate_path' in d else ''
        self.certificate_path = dcp

    def get_schema(self, host_url=''):
        """Return hackathon.json formatted metadata."""
        desc = self.summary or re.sub('<[^>]*>', '', self.description or '')
        d = {
            "@context": "http://schema.org",
            "@type": "Event",
            "name": self.name,
            "url": host_url + self.url,
            "description": desc,
            "startDate": format_date(self.starts_at, '%Y-%m-%dT%H:%M'),
            "endDate": format_date(self.ends_at, '%Y-%m-%dT%H:%M'),
            "workPerformed": [p.get_schema(host_url) for p in self.projects]
        }
        if self.hostname and self.location:
            d["location"] = {
                "@type": "Place",
                "name": self.hostname, "address": self.location
            }
        if self.logo_url:
            d["logo"] = self.logo_url
        if self.webpage_url:
            d["mainEntityOfPage"] = self.webpage_url
            d["offers"] = {"@type": "Offer", "url": self.webpage_url}
        return d

    @property
    def url(self):
        """Extra property."""
        return "event/%d" % (self.id)

    @property
    def background_image(self):
        """Fetch first gallery image if available."""
        return self.gallery_url.split(',')[0] or ''

    @property
    def has_started(self):
        """Extra property."""
        return self.starts_at <= dt.datetime.utcnow() <= self.ends_at

    @property
    def has_finished(self):
        """Extra property."""
        return dt.datetime.utcnow() > self.ends_at

    @property
    def can_start_project(self):
        """Extra property."""
        return not self.has_finished and not self.lock_starting

    @property
    def ends_at_tz(self):
        """Extra property."""
        return current_app.tz.localize(self.ends_at)

    @property
    def starts_at_tz(self):
        """Extra property."""
        return current_app.tz.localize(self.starts_at)

    @property
    def countdown(self):
        """Provide a normalized countdown timer."""
        starts_at = current_app.tz.localize(self.starts_at)
        ends_at = current_app.tz.localize(self.ends_at)
        # Check event time limit (hard coded to 30 days)
        tz_now = current_app.tz.localize(dt.datetime.utcnow())
        time_limit = tz_now + dt.timedelta(days=30)
        # Show countdown within limits
        if starts_at > tz_now:
            if starts_at > time_limit:
                return None
            return starts_at
        elif ends_at > tz_now:
            if ends_at > time_limit:
                return None
            return ends_at
        else:
            return None

    @property
    def date(self):
        """Get a formatted date range."""
        return format_date_range(self.starts_at, self.ends_at)

    @property
    def oneliner(self):
        """Return short online description."""
        ol = self.summary or self.description or ''
        ol = re.sub(r"\s+", " ", ol)
        if len(ol) > 140:
            ol = ol[:140] + '...'
        return ol

    @property
    def project_count(self):
        """Return number of projects."""
        if not self.projects:
            return 0
        return len(self.projects)

    def categories_for_event(self):
        """Event categories."""
        return Category.query.filter(or_(
            Category.event_id is None,
            Category.event_id == -1,
            Category.event_id == self.id
        )).order_by('name')

    @property
    def has_categories(self):
        """Check if the event has categories to show."""
        return self.categories_for_event().count() > 0

    def current():
        """Return currently featured event."""
        # TODO: allow multiple featurettes?
        return Event.query.filter_by(is_current=True).first()

    def __init__(self, name=None, **kwargs):  # noqa: D107
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):  # noqa: D105
        return '<Event({name})>'.format(name=self.name)


class Project(PkModel):
    """You know, for kids."""

    __versioned__ = {}
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
    # remotely managed (by bot)
    is_autoupdate = Column(db.Boolean(), default=True)

    autotext = Column(db.UnicodeText(), nullable=True, default=u"")
    longtext = Column(db.UnicodeText(), nullable=False, default=u"")

    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(40), nullable=True)

    created_at = Column(db.DateTime, nullable=False,
                        default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False,
                        default=dt.datetime.utcnow)

    # User who created the project
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='projects')

    # Event under which this project belongs
    event_id = reference_col('events', nullable=True)
    event = relationship('Event', backref='projects')

    # An optional event category
    category_id = reference_col('categories', nullable=True)
    category = relationship('Category', backref='projects')

    # Assessment and total score
    progress = Column(db.Integer(), nullable=True, default=-1)
    score = Column(db.Integer(), nullable=True, default=0)

    @property
    def team(self):
        """Array of project team."""
        return [u.username for u in self.get_team()]

    @property
    def stage(self):
        """Assessment of progress stage with full data."""
        return getStageByProgress(self.progress)

    @property
    def phase(self):
        """Assessment of progress as phase name."""
        return getProjectPhase(self)

    @property
    def is_challenge(self):
        """Return True if this project is in challenge phase."""
        if self.progress is None:
            return False
        return self.progress <= PR_CHALLENGE

    @property
    def is_autoupdateable(self):
        """Return True if this project can be autoupdated."""
        return self.autotext_url and self.autotext_url.strip()

    @property
    def webembed(self):
        """Detect and return supported embed widgets."""
        return format_webembed(self.id, self.webpage_url)

    @property
    def longhtml(self):
        """Process project longtext and return HTML."""
        if not self.longtext or len(self.longtext) < 3:
            return self.longtext
        # TODO: apply onebox filter
        # TODO: apply markdown filter
        return self.longtext

    @property
    def url(self):
        """Return local server URL."""
        return "project/%d" % (self.id)

    @property
    def data(self):
        """Get JSON representation."""
        d = {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'team': self.team,
            'score': self.score,
            'phase': self.phase,
            'is_challenge': self.is_challenge,
            'is_webembed': self.is_webembed,
            'progress': self.progress,
            'summary': self.summary or '',
            'hashtag': self.hashtag or '',
            'image_url': self.image_url or '',
            'source_url': self.source_url or '',
            'webpage_url': self.webpage_url or '',
            'autotext_url': self.autotext_url or '',
            'download_url': self.download_url or '',
            'contact_url': self.contact_url or '',
            'logo_color': self.logo_color or '',
            'logo_icon': self.logo_icon or '',
            'excerpt': '',
        }
        d['created_at'] = format_date(self.created_at, '%Y-%m-%dT%H:%M')
        d['updated_at'] = format_date(self.updated_at, '%Y-%m-%dT%H:%M')
        # Generate excerpt based on summary data
        if self.longtext and len(self.longtext) > 10:
            d['excerpt'] = self.longtext[:MAX_EXCERPT_LENGTH]
            if len(self.longtext) > MAX_EXCERPT_LENGTH:
                d['excerpt'] += '...'
        elif self.is_autoupdateable:
            if self.autotext and len(self.autotext) > 10:
                d['excerpt'] = self.autotext[:MAX_EXCERPT_LENGTH]
                if len(self.autotext) > MAX_EXCERPT_LENGTH:
                    d['excerpt'] += '...'
        if self.user is not None:
            d['maintainer'] = self.user.username
        if self.event is not None:
            d['event_url'] = self.event.url
            d['event_name'] = self.event.name
        if self.category is not None:
            d['category_id'] = self.category.id
            d['category_name'] = self.category.name
        return d

    def latest_activity(self, max=5):
        """Query for latest activity."""
        q = Activity.query.filter_by(project_id=self.id)
        q = q.order_by(Activity.timestamp.desc())
        return q.limit(max)

    def get_team(self, with_spectators=False):
        """Return all starring users (A team)."""
        q = Activity.query.filter_by(project_id=self.id)
        if with_spectators:
            activities = q.all()
        else:
            activities = q.filter_by(name='star').all()
        members = []
        for a in activities:
            if a.user and a.user not in members:
                members.append(a.user)
        return members

    def get_stats(self):
        """Collect some activity stats."""
        q = Activity.query.filter_by(project_id=self.id)
        s_total = q.count()
        s_updates = q.filter_by(
            name='update'
        ).count()
        s_commits = q.filter_by(
            name='update', action='commit'
        ).count()
        if self.event:
            s_during = q.filter(
                Activity.timestamp > self.event.starts_at_tz,
                Activity.timestamp < self.event.ends_at_tz
            ).count()
        else:
            s_during = 0
        s_people = len(self.get_team(True))
        # TODO: real wordcount
        s_words = len(self.longtext.split(' '))
        s_allwords = s_words + len(self.autotext.split(' '))
        s_allwords = s_allwords + len(self.summary.split(' '))
        return {
            'total':    s_total,
            'updates':  s_updates,
            'commits':  s_commits,
            'during':   s_during,
            'people':   s_people,
            'words':    s_words,
            'allwords': s_allwords,
        }

    def get_missing_roles(self):
        """List all roles which are not yet in team."""
        get_roles = Role.query.order_by('name')
        rollcall = []
        for p in self.get_team():
            for r in p.roles:
                if r not in rollcall:
                    rollcall.append(r)
        return [r for r in get_roles if r not in rollcall and r.name]

    def all_dribs(self):
        """Query which formats the project's timeline."""
        activities = Activity.query.filter_by(
                        project_id=self.id
                    ).order_by(Activity.timestamp.desc())
        dribs = []
        prev = None
        only_active = False  # show dribs from inactive users
        for a in activities:
            a_parsed = getActivityByType(a, only_active)
            if a_parsed is None:
                continue
            (author, title, text, icon) = a_parsed
            if prev is not None:
                # Skip repeat signals
                if prev['title'] == title and prev['text'] == text:
                    # if prev['date']-a.timestamp).total_seconds() < 120:
                    continue
                # Show changes in progress
                if prev['progress'] != a.project_progress:
                    proj_stage = getStageByProgress(a.project_progress)
                    if proj_stage is not None:
                        dribs.append({
                            'title': proj_stage['phase'],
                            'date': a.timestamp,
                            'icon': 'arrow-up',
                            'name': 'progress',
                        })
            prev = {
                'icon': icon,
                'title': title,
                'text': text,
                'author': author,
                'name': a.name,
                'date': a.timestamp,
                'ref_url': a.ref_url,
                'progress': a.project_progress,
                'id': a.id,
            }
            dribs.append(prev)
        if self.event.has_started or self.event.has_finished:
            dribs.append({
                'title': "Event started",
                'date': self.event.starts_at,
                'icon': 'calendar',
                'name': 'start',
            })
        if self.event.has_finished:
            dribs.append({
                'title': "Event finished",
                'date': self.event.ends_at,
                'icon': 'bullhorn',
                'name': 'finish',
            })
        return sorted(dribs, key=lambda x: x['date'], reverse=True)

    def categories_all(self, event=None):
        """Return convenience query for all categories."""
        if self.event:
            return self.event.categories_for_event()
        if event is not None:
            return event.categories_for_event()
        return Category.query.order_by('name')

    def get_schema(self, host_url=''):
        """Schema.org compatible metadata."""
        # TODO: accurately detect project license based on component etc.
        if not self.event.community_embed:
            content_license = ''
        elif "creativecommons" in self.event.community_embed:
            content_license = "https://creativecommons.org/licenses/by/4.0/"
        else:
            content_license = ''
        cleansummary = None
        if self.summary:
            cleansummary = re.sub('<[^>]*>', '', self.summary)
        return {
            "@type": "CreativeWork",
            "name": self.name,
            "description": cleansummary,
            "dateCreated": format_date(self.created_at, '%Y-%m-%dT%H:%M'),
            "dateUpdated": format_date(self.updated_at, '%Y-%m-%dT%H:%M'),
            "discussionUrl": self.contact_url,
            "image": self.image_url,
            "license": content_license,
            "url": host_url + self.url
        }

    def set_from_data(self, data):
        """Update from JSON representation."""
        self.name = data['name']
        self.summary = data['summary']
        self.hashtag = data['hashtag']
        self.image_url = data['image_url']
        self.source_url = data['source_url']
        self.webpage_url = data['webpage_url']
        self.autotext_url = data['autotext_url']
        self.download_url = data['download_url']
        self.contact_url = data['contact_url']
        self.logo_color = data['logo_color']
        self.logo_icon = data['logo_icon']
        self.longtext = data['longtext']
        self.autotext = data['autotext']
        self.score = int(data['score'] or 0)
        self.progress = int(data['progress'] or 0)
        try:
            self.created_at = parse(data['created_at'])
            self.updated_at = parse(data['updated_at'])
        except ParserError as ex:
            self.created_at = dt.datetime.utcnow()
            self.updated_at = dt.datetime.utcnow()
            print(ex)
        if 'is_autoupdate' in data:
            self.is_autoupdate = data['is_autoupdate']
        if 'is_webembed' in data:
            self.is_webembed = data['is_webembed']
        if 'maintainer' in data:
            uname = data['maintainer']
            user = User.query.filter_by(username=uname).first()
            if user:
                self.user = user
        if 'category_name' in data:
            cname = data['category_name']
            category = Category.query.filter_by(name=cname).first()
            if category:
                self.category = category

    def update(self):
        """Process data submission."""
        # Correct fields
        if self.category_id == -1:
            self.category_id = None
        if self.logo_icon and self.logo_icon.startswith('fa-'):
            self.logo_icon = self.logo_icon.replace('fa-', '')
        if self.logo_color == '#000000':
            self.logo_color = ''
        # Set the timestamp
        self.updated_at = dt.datetime.utcnow()
        self.update_null_fields()
        self.score = self.calculate_score()

    def update_null_fields(self):
        """Reset fields in None-state."""
        if self.summary is None:
            self.summary = ''
        if self.image_url is None:
            self.image_url = ''
        if self.source_url is None:
            self.source_url = ''
        if self.webpage_url is None:
            self.webpage_url = ''
        if self.logo_color is None:
            self.logo_color = ''
        if self.logo_icon is None:
            self.logo_icon = ''
        if self.longtext is None:
            self.longtext = ''
        if self.autotext is None:
            self.autotext = ''

    def calculate_score(self):  # noqa: C901
        """Calculate score of a project based on base progress."""
        if self.is_challenge:
            return 0
        score = self.progress or 0
        cqu = Activity.query.filter_by(project_id=self.id)
        c_s = cqu.count()
        # Get a point for every (join, update, comment ..) activity in dribs
        score = score + (1 * c_s)
        # Extra point for every boost (upvote)
        c_a = cqu.filter_by(name="boost").count()
        score = score + (1 * c_a)
        # Add to the score for every complete documentation field
        score = score + 1 * int(len(self.summary) > 3)
        score = score + 1 * int(len(self.image_url) > 3)
        score = score + 1 * int(len(self.source_url) > 3)
        score = score + 1 * int(len(self.webpage_url) > 3)
        score = score + 1 * int(len(self.logo_color) > 3)
        score = score + 1 * int(len(self.logo_icon) > 3)
        # Get more points based on how much content you share
        score = score + 1 * int(len(self.longtext) > 3)
        score = score + 3 * int(len(self.longtext) > 100)
        score = score + 5 * int(len(self.longtext) > 500)
        # Points for external (Readme) content
        score = score + 1 * int(len(self.autotext) > 3)
        score = score + 3 * int(len(self.autotext) > 100)
        score = score + 5 * int(len(self.autotext) > 500)
        # Cap at 100%
        score = min(score, 100)
        return score

    def __init__(self, name=None, **kwargs):  # noqa: D107
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):  # noqa: D105
        return '<Project({name})>'.format(name=self.name)


class Category(PkModel):
    """Is it a bird? Is it a plane?."""

    __tablename__ = 'categories'
    name = Column(db.String(80), nullable=False)
    description = Column(db.UnicodeText(), nullable=True)
    logo_color = Column(db.String(7), nullable=True)
    logo_icon = Column(db.String(20), nullable=True)

    # If specific to an event
    event_id = reference_col('events', nullable=True)
    event = relationship('Event', backref='categories')

    def project_count(self):
        """Count projects in this Category."""
        if not self.projects:
            return 0
        return len(self.projects)

    @property
    def data(self):
        """Get JSON representation."""
        d = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'logo_color': self.logo_color,
            'logo_icon': self.logo_icon,
        }
        if self.event:
            d['event_id'] = self.event_id
            d['event_name'] = self.event.name
            d['event_url'] = self.event.url
        return d

    def set_from_data(self, data):
        """Update from a JSON representation."""
        self.name = data['name']
        if 'description' in data:
            self.description = data['description']
        if 'logo_color' in data:
            self.logo_color = data['logo_color']
        if 'logo_icon' in data:
            self.logo_icon = data['logo_icon']
        if 'event_name' in data:
            ename = data['event_name']
            evt = Event.query.filter_by(name=ename).first()
            if evt:
                self.event = evt

    def __init__(self, name=None, **kwargs):  # noqa: D107
        if name:
            db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):  # noqa: D105
        return '<Category({name})>'.format(name=self.name)


class Activity(PkModel):
    """Public, real time, conversational."""

    __tablename__ = 'activities'
    name = Column(db.Enum('review',
                          'boost',
                          'create',
                          'update',
                          'star',
                          name="activity_type"))
    action = Column(db.String(32), nullable=True)
    # 'external', 'commit', 'sync', 'post', ...
    timestamp = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    content = Column(db.UnicodeText, nullable=True)
    ref_url = Column(db.String(2048), nullable=True)

    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='activities')

    project_id = reference_col('projects', nullable=True)
    project = relationship('Project', backref='activities')
    project_progress = Column(db.Integer, nullable=True)
    project_version = Column(db.Integer, nullable=True)
    project_score = Column(db.Integer, nullable=True)

    @property
    def data(self):
        """Get JSON representation."""
        localtime = current_app.tz.localize(self.timestamp)
        a = {
            'id': self.id,
            'time': int(mktime(self.timestamp.timetuple())),
            'date': format_date(localtime, '%Y-%m-%dT%H:%M'),
            'timesince': timesince(localtime),
            'name': self.name,
            'action': self.action or '',
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

    def set_from_data(self, data):
        """Update from a JSON representation."""
        self.name = data['name']
        self.action = data['action']
        self.content = data['content']
        self.ref_url = data['ref_url']
        self.timestamp = dt.datetime.fromtimestamp(data['time'])
        if 'user_name' in data:
            uname = data['user_name']
            user = User.query.filter_by(username=uname).first()
            if user:
                self.user = user

    def may_delete(self, user):
        """Check permission for deleting post."""
        userok = (self.user and user == self.user and user.active)
        return userok or user.is_admin

    def __init__(self, name, project_id, **kwargs):  # noqa: D107
        if name:
            db.Model.__init__(
                self, name=name,
                project_id=project_id,
                **kwargs
            )

    def __repr__(self):  # noqa: D105
        return '<Activity({name})>'.format(name=self.name)


class Resource(PkModel):
    """Somewhat graph-like in principle."""

    __tablename__ = 'resources'
    name = Column(db.String(80), nullable=False)
    type_id = Column(db.Integer(), nullable=True, default=0)

    created_at = Column(db.DateTime, nullable=False,
                        default=dt.datetime.utcnow)
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
    def of_type(self):  # noqa: D102
        return getResourceType(self)

    @property
    def data(self):
        """Get JSON representation."""
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

    def __init__(self, name, project_id, **kwargs):  # noqa: D107
        db.Model.__init__(
            self, name=name, project_id=project_id,
            **kwargs
        )

    def __repr__(self):  # noqa: D105
        return '<Resource({name})>'.format(name=self.name)
