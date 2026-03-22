from dribdat.app import init_app
from dribdat.settings import DevConfig
from dribdat.database import db
from dribdat.user.models import User, Event, Project, Resource
from datetime import datetime, timedelta
from dribdat.futures import UTC

app = init_app(DevConfig)
with app.app_context():
    # Create admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('password')
        admin.is_admin = True
        admin.active = True
        admin.save()

    # Create Bootstrap event
    event = Event.query.filter_by(name='Test Bootstraps').first()
    if not event:
        event = Event(name='Test Bootstraps')
        event.lock_resources = True
        event.starts_at = datetime.now(UTC) - timedelta(days=1)
        event.ends_at = datetime.now(UTC) + timedelta(days=1)
        event.save()

    # Create project
    project = Project.query.filter_by(name='Test Project').first()
    if not project:
        project = Project(name='Test Project', event_id=event.id)
        project.user_id = admin.id
        project.progress = 10
        project.save()

    # Add resource
    res = Resource.query.filter_by(name='Test Model').first()
    if not res:
        res = Resource(name='Test Model', project_id=project.id, type='model', description='A test AI model')
        res.save()

    print("Test data created successfully.")
