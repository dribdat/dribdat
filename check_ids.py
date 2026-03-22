from dribdat.app import init_app
from dribdat.settings import DevConfig
from dribdat.user.models import User, Event, Project, Resource

app = init_app(DevConfig)
with app.app_context():
    for u in User.query.all(): print(f"User: {u.id} {u.username}")
    for e in Event.query.all(): print(f"Event: {e.id} {e.name}")
    for p in Project.query.all(): print(f"Project: {p.id} {p.name}")
