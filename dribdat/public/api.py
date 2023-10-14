# -*- coding: utf-8 -*-
"""API calls for dribdat."""
import boto3
import tempfile
import datetime as dt

from flask import (
    Blueprint, current_app,
    Response, request, redirect,
    stream_with_context, send_file,
    jsonify, flash, url_for, escape
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from ..extensions import db, cache
from ..utils import timesince, random_password, sanitize_url
from ..decorators import admin_required
from ..user.models import Event, Project, Activity, User
from ..apipackage import import_event_package, event_to_data_package
from ..aggregation import (
    AddProjectDataFromAutotext,
    GetProjectData, 
    GetEventUsers,
)
from ..apiutils import (
    get_project_list,
    get_event_activities,
    get_schema_for_user_projects,
    expand_project_urls,
    gen_csv,
)
from ..apipackage import (
    fetch_datapackage, import_datapackage
)

blueprint = Blueprint('api', __name__, url_prefix='/api')


# ------ EVENT INFORMATION ---------

@blueprint.route('/event/current/info.json')
def info_current_event_json():
    """Output JSON about the current event."""
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    timeuntil = timesince(event.countdown, until=True)
    return jsonify(event=event.data, timeuntil=timeuntil)


@blueprint.route('/event/<int:event_id>/info.json')
def info_event_json(event_id):
    """Output JSON about an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    timeuntil = timesince(event.countdown, until=True)
    return jsonify(event=event.data, timeuntil=timeuntil)


@blueprint.route('/event/<int:event_id>/hackathon.json')
def info_event_hackathon_json(event_id):
    """Output JSON-LD about an Event according to schema."""
    """See https://schema.org/Hackathon."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(event.get_schema(request.host_url))


# ------ EVENT PROJECTS ---------

def request_project_list(event_id):
    """Fetch a project list."""
    is_moar = bool(request.args.get('moar', type=bool))
    host_url = request.host_url
    return get_project_list(event_id, host_url, is_moar)


@blueprint.route('/event/current/projects.json')
def project_list_current_json():
    """Output JSON of projects in the current event with its info."""
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    return jsonify(projects=request_project_list(event.id), event=event.data)


@blueprint.route('/event/<int:event_id>/projects.json')
def project_list_json(event_id):
    """Output JSON of all projects at a specific event."""
    return jsonify(projects=request_project_list(event_id))


def project_list_csv(event_id, event_name):
    """Fetch a CSV file with projects for an event."""
    headers = {
        'Content-Disposition': 'attachment; filename='
        + event_name + '_projects_dribdat.csv'
    }
    csvlist = gen_csv(request_project_list(event_id))
    return Response(stream_with_context(csvlist),
                    mimetype='text/csv',
                    headers=headers)


@blueprint.route('/event/<int:event_id>/projects.csv')
def project_list_event_csv(event_id):
    """Output CSV of all projects in an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    return project_list_csv(event.id, event.name)


@blueprint.route('/event/current/projects.csv')
def project_list_current_csv():
    """Output CSV of projects and challenges in the current event."""
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    return project_list_csv(event.id, event.name)


@blueprint.route('/events.<as_format>')
def list_all_events(as_format='json'):
    """Output basic data of all public events."""
    eventlist = []
    for event in Event.query \
            .filter_by(is_hidden=False, lock_resources=False) \
            .order_by(Event.starts_at.desc()).all():
        eventlist.append(event.data)
    if as_format == 'json':
        return jsonify(events=eventlist)
    headers = {'Content-Disposition': 'attachment; filename=events.csv'}
    csvlist = gen_csv(eventlist)
    return Response(stream_with_context(csvlist),
                    mimetype='text/csv',
                    headers=headers)


@blueprint.route('/events/projects.csv')
def project_list_all_events_csv():
    """Output CSV of projects and challenges in all events."""
    projectlist = []
    export = Event.query.filter_by(is_hidden=False, lock_resources=False).all()
    for event in export:
        projectlist.extend(request_project_list(event.id))
    headers = {'Content-Disposition': 'attachment; filename=projects.csv'}
    csvlist = gen_csv(projectlist)
    return Response(stream_with_context(csvlist),
                    mimetype='text/csv',
                    headers=headers)


@blueprint.route('/event/current/categories.json')
def categories_list_current_json():
    """Output JSON of categories in the current event."""
    event = Event.query.filter_by(is_current=True).first()
    categories = [c.data for c in event.categories_for_event()]
    return jsonify(categories=categories, event=event.data)

# ------ ACTIVITIES ---------


@blueprint.route('/event/<int:event_id>/activity.json')
def event_activity_json(event_id):
    """Output JSON of recent activity in an event."""
    limit = request.args.get('limit') or 50
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    return jsonify(activities=get_event_activities(event_id, limit, q))


@blueprint.route('/event/current/activity.json')
def event_activity_current_json():
    """Output JSON of categories in the current event."""
    event = Event.query.filter_by(is_current=True).first()
    if not event:
        return jsonify(activities=[])
    return event_activity_json(event.id)


@blueprint.route('/event/<int:event_id>/activity.csv')
def event_activity_csv(event_id):
    """Output CSV of an event activity."""
    limit = request.args.get('limit') or 50
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    csvstream = gen_csv(get_event_activities(event_id, limit, q))
    headers = {'Content-Disposition': 'attachment; filename=activity_list.csv'}
    return Response(stream_with_context(csvstream),
                    mimetype='text/csv', headers=headers)


@blueprint.route('/project/activity.json')
def projects_activity_json():
    """Output JSON of recent activity across all projects."""
    limit = request.args.get('limit') or 10
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    return jsonify(activities=get_event_activities(None, limit, q))


@blueprint.route('/project/posts.json')
def projects_posts_json():
    """Output JSON of recent posts (activity) across projects."""
    limit = request.args.get('limit') or 10
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    return jsonify(activities=get_event_activities(None, limit, q, "post"))


@blueprint.route('/project/top.json')
def projects_top_json():
    """Output the top projects."""
    limit = request.args.get('limit') or 10
    #sort_by_score = request.args.get('score') or False
    #sort_by_update = request.args.get('update') or False
    pp = Project.query \
            .filter_by(is_hidden=False) \
            .order_by(Project.progress.desc()) \
            .limit(limit).all()
    projects = expand_project_urls(
        [p.data for p in pp],
        request.host_url
    )
    return jsonify(projects=projects)


@blueprint.route('/project/<int:project_id>/activity.json')
def project_activity_json(project_id):
    """Output JSON of recent activity of a project."""
    limit = request.args.get('limit') or 10
    project = Project.query.filter_by(id=project_id).first_or_404()
    query = Activity.query.filter_by(project_id=project.id).order_by(
        Activity.id.desc()).limit(limit).all()
    activities = [a.data for a in query]
    return jsonify(project=project.data, activities=activities)


@blueprint.route('/project/<int:project_id>')
@blueprint.route('/project/<int:project_id>/info.json')
def project_info_json(project_id):
    """Output JSON info for a specific project."""
    is_full = bool(request.args.get('full')) or False
    project = Project.query.filter_by(id=project_id).first_or_404()
    team = []
    for user in project.get_team():
        team.append({
            'id': user.id,
            'name': user.username,
            'link': user.webpage_url
        })
    data = {
        'project': project.data,
        'phase': project.phase,
        'pitch': project.webembed,
        'is_webembed': project.is_webembed,
        'event': project.event.data,
        'stats': project.get_stats(),
        'team': team
    }
    if is_full:
        data['project']['autotext'] = project.autotext  # Markdown
        data['project']['longtext'] = project.longtext  # Markdown - see longhtml()
    if project.user:
        data['creator'] = {
            'id': project.user.id,
            'username': project.user.username
        }
    return jsonify(data)

# ------ USERS ----------


@blueprint.route('/event/<int:event_id>/participants.csv')
@admin_required
def event_participants_csv(event_id):
    """Download a CSV of event participants."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    userlist = [u.data for u in GetEventUsers(event)]
    headers = {
        'Content-Disposition': 'attachment; '
        + 'filename=user_list_%d.csv' % event.id
    }
    return Response(stream_with_context(gen_csv(userlist)),
                    mimetype='text/csv',
                    headers=headers)


# ------ SEARCH ---------

@blueprint.route('/project/search.json')
def project_search_json():
    """Run a full text search on projects."""
    q = request.args.get('q')
    if q is None or len(q) < 3:
        return jsonify(projects=[])
    limit = request.args.get('limit') or 10
    q = "%%%s%%" % q
    projects = Project.query.filter(or_(
        Project.name.like(q),
        Project.summary.like(q),
        Project.longtext.like(q),
        Project.autotext.like(q),
    )).limit(limit).all()
    projects = expand_project_urls(
        [p.data for p in projects],
        request.host_url
    )
    return jsonify(projects=projects)

# ------ UPDATE ---------


@blueprint.route('/event/load/datapackage', methods=["POST"])
@admin_required
def event_upload_datapackage():
    """Load event data from an uploaded Data Package."""
    filedata = request.files['file']
    import_level = request.form.get('import')
    if not filedata or not import_level:
        return jsonify(status='Error', errors=['Missing import data parameters'])
    # Check link
    if 'datapackage.json' not in filedata.filename:
        return jsonify(status='Error', errors=['Must be a datapackage.json'])
    # Configuration
    dry_run = True
    all_data = False
    status = "Preview"
    if import_level == 'basic':
        dry_run = False
        status = "Basic"
    if import_level == 'full':
        dry_run = False
        all_data = True
        status = "Complete"
    # File handling
    results = import_datapackage(filedata, dry_run, all_data)
    event_names = ', '.join([r['name'] for r in results['events']])
    if 'errors' in results:
        return jsonify(status='Error', errors=results['errors'])
    else:
        flash("Events uploaded: %s" % event_names, 'success')
        return redirect(url_for("admin.events"))
    return jsonify(status=status, results=results)


@blueprint.route('/event/push/datapackage', methods=["PUT", "POST"])
def event_push_datapackage():
    """Upload event data from a Data Package."""
    key = request.headers.get('key')
    if not key or key != current_app.config['SECRET_API']:
        return jsonify(status='Error', errors=['Invalid API key'])
    data = request.get_json(force=True)
    results = import_event_package(data)
    if 'errors' in results:
        return jsonify(status='Error', errors=results['errors'])
    return jsonify(status='Complete', results=results)


@blueprint.route('/event/current/get/status', methods=["GET"])
def event_get_status():
    """Get current event status."""
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first()
    if not event:
        return jsonify(status='')
    return jsonify(status=event.status_text or '')


@blueprint.route('/event/<int:event_id>/push/status', methods=["PUT", "POST"])
@admin_required
def event_push_status(event_id):
    """Update event status."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    newstatus = request.form.get('text')
    if not request.form.get('text'): 
        # Clear the status
        event.status = None
    else:
        # Update the status
        event.status = str(dt.datetime.now().timestamp()) + ';' \
            + newstatus.replace(';', ':')
    event.save()
    return jsonify(status='OK')


@blueprint.route('/project/push.json', methods=["PUT", "POST"])
def project_push_json():
    """Push data into a project."""
    data = request.get_json(force=True)
    if 'key' not in data or data['key'] != current_app.config['SECRET_API']:
        return jsonify(error='Invalid key')
    project = Project.query.filter_by(hashtag=data['hashtag']).first()
    if not project:
        project = Project()
        project.user_id = 1
        project.progress = 0
        project.is_autoupdate = True
        project.event = Event.query.filter_by(is_current=True).first()
    elif project.user_id != 1 or project.is_hidden:
        return jsonify(error='Access denied')
    set_project_values(project, data)
    project.update_now()
    project.save()
    db.session.commit()
    return jsonify(success='Updated', project=project.data)


def set_project_values(project, data):
    """Convert a data object to model values."""
    project.hashtag = data['hashtag']
    if 'name' in data and len(data['name']) > 0:
        project.name = data['name']
    else:
        project.name = project.hashtag.replace('-', ' ')
    if 'summary' in data and len(data['summary']) > 0:
        project.summary = data['summary']
    has_longtext = 'longtext' in data and len(data['longtext']) > 0
    if has_longtext:
        project.longtext = data['longtext']
    if 'autotext_url' in data and data['autotext_url'].startswith('http'):
        project.autotext_url = data['autotext_url']
        if not project.source_url or project.source_url == '':
            project.source_url = data['autotext_url']
    # MAX progress
    if 'levelup' in data and 0 < project.progress + data['levelup'] * 10 < 50:
        project.progress = project.progress + data['levelup'] * 10
    # return jsonify(data=data)
    if project.autotext_url is not None and not has_longtext:
        # Now try to autosync
        AddProjectDataFromAutotext(project)
    return project


# ------ FRONTEND -------

@blueprint.route('/project/autofill', methods=['GET', 'POST'])
@login_required
def project_autofill():
    """Routine used to help sync project data."""
    url = sanitize_url(request.args.get('url'))
    data = GetProjectData(url)
    return jsonify(data)

# ------ UPLOADING -------

# TODO: move to separate upload.py ?


ACCEPTED_TYPES = [
    'png', 'jpg', 'jpeg', 'gif', 'webp',  # ʕ·͡ᴥ·ʔ
    'json', 'geojson',                    # ( ͡° ͜ʖ ͡°)
    'csv', 'tsv',                         # ¯\_(ツ)_/¯
    'ods', 'pdf', 'svg'                   # (ノಠ ∩ಠ)ノ彡
]


@blueprint.route('/project/uploader', methods=["POST"])
@login_required
def project_uploader():
    """Enable uploading images and files into a project."""
    if not current_app.config['S3_KEY']:
        return ''
    if len(request.files) == 0:
        return 'No files selected'
    img = request.files['file']
    if not img or img.filename == '':
        return 'No filename'
    ext = img.filename.split('.')[-1].lower()
    if ext not in ACCEPTED_TYPES:
        return 'Invalid format (allowed: %s)' % ','.join(ACCEPTED_TYPES)
    # generate a simpler filename
    keepcharacters = ('.', '_')
    safe_filename = img.filename.replace(' ', '_')
    safe_filename = "".join(
        c for c in safe_filename
        if c.isalnum() or c in keepcharacters).rstrip()
    if not safe_filename:
        safe_filename = "".join(random_password(8), '.', ext)
    # use random subfolder inside user id folder
    filename = '/'.join([
                    str(current_user.id),
                    random_password(24),
                    safe_filename
                ])
    # with tempfile.TemporaryDirectory() as tmpdir:
    #   img.save(path.join(tmpdir, filename))
    if 'S3_FOLDER' in current_app.config:
        s3_filepath = '/'.join([current_app.config['S3_FOLDER'], filename])
    else:
        s3_filepath = filename
    # print('Uploading to %s' % s3_filepath)
    if 'S3_ENDPOINT' in current_app.config:
        s3_obj = boto3.client(
            service_name='s3',
            endpoint_url=current_app.config['S3_ENDPOINT'],
            aws_access_key_id=current_app.config['S3_KEY'],
            aws_secret_access_key=current_app.config['S3_SECRET'],
        )
        #print('Uploading to endpoint %s' % current_app.config['S3_ENDPOINT'])
    else:
        s3_obj = boto3.client(
            service_name='s3',
            region_name=current_app.config['S3_REGION'],
            aws_access_key_id=current_app.config['S3_KEY'],
            aws_secret_access_key=current_app.config['S3_SECRET'],
        )
        #print('Uploading to region %s' % current_app.config['S3_REGION'])
    # Commence upload
    s3_obj.upload_fileobj(img,
                          current_app.config['S3_BUCKET'],
                          s3_filepath,
                          ExtraArgs={'ContentType': img.content_type,
                                     'ACL': 'public-read'}
                          )
    return escape('/'.join([current_app.config['S3_HTTPS'], s3_filepath]))


# ------ DATA PACKAGE API --------


def generate_event_package(event, format='json'):
    """Create a Data Package from the data of an event."""
    if format not in ['zip', 'json']:
        return "Format not supported"
    full_contents = (format == 'zip')
    host_url = request.host_url
    package = event_to_data_package(event, current_user, host_url, full_contents)
    if format == 'json':
        # Generate JSON representation
        return jsonify(package)
    elif format == 'zip':
        # Build a file reference
        filename = "datapackage-%s-" % event.name.lower().strip()
        # Generate data package file
        fp_package = tempfile.NamedTemporaryFile(
            prefix=filename, suffix='.zip')
        package.to_zip(fp_package.name)
        return send_file(fp_package.name, as_attachment=True)

@blueprint.route('/event/current/datapackage.<format>', methods=["GET"])
@cache.cached()
def package_current_event(format):
    """Download a Data Package for an event."""
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    return generate_event_package(event, format)


@blueprint.route('/event/<int:event_id>/datapackage.<format>', methods=["GET"])
@cache.cached()
def package_specific_event(event_id, format):
    """Download a Data Package for an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    return generate_event_package(event, format)


# ------ USER API --------


@blueprint.route('/user/current/my-hackathons.json', methods=['GET'])
def current_user_hackathon_json():
    """Output JSON-LD about a User's Event according to schema."""
    """See https://schema.org/Hackathon."""
    host_url = request.host_url
    data = get_schema_for_user_projects(current_user, host_url)
    return jsonify(data)


@blueprint.route('/user/current/profile.json', methods=['GET'])
def profile_user_current_json():
    """Output JSON with public data about the current user."""
    if current_user and not current_user.is_anonymous:
        return profile_user_json(current_user.id)
    return jsonify({'message': 'Not logged in', 'status': 'error'})


def get_user_data(current_user):
    """Retrieves public data for a user."""
    current_data = current_user.data
    current_data['score'] = current_user.get_score()
    del current_data['email']
    del current_data['sso_id']
    del current_data['is_admin']
    return current_data


@blueprint.route('/user/<int:user_id>/profile.json', methods=['GET'])
def profile_user_json(user_id: int):
    """Output JSON with public data about a user."""
    current_user = User.query.filter_by(id=user_id).first_or_404()
    return jsonify(get_user_data(current_data))


@blueprint.route('/user/<username>', methods=['GET'])
def profile_username_json(username):
    """Output JSON with public data by username."""
    a_user = User.query.filter_by(username=username).first_or_404()
    return jsonify(get_user_data(a_user))


# ------ FEEDS ---------

# TODO: 600+ lines of API bootstrap deserve a refactor.

@blueprint.route('/feed/<username>', methods=['GET'])
def feed_user(username):
    """Output ActivityPub with public data by username."""
    a_user = User.query.filter_by(username=username).first_or_404()
    url_user = url_for("public.user", username=a_user.username, _external=True)
    url_here = url_for("api.feed_user", username=a_user.username, _external=True)
    apub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": url_user,
        "inbox": url_here + '/inbox'
        "outbox": url_here + '/activities',
        "type": "Person",
        "name": a_user.name,
        "preferredUsername": a_user.username,
        "publicKey": {
            "id": url_user + "#main-key",
            "publicKeyPem": public_key
        }
    }
    resp = Response(jsonify(apub))
    resp.headers['Content-Type'] = 'application/activity+json'
    return resp


@blueprint.route('/feed/<username>/inbox', methods=['POST'])
def feed_user_inbox(username):
    current_app.logger.info(request.headers)
    current_app.logger.info(request.data)
    return Response("", status=202)


@blueprint.route('/feed/<username>/activities', methods=['GET'])
def feed_user_activities(username):
    activities = []
    url_user = url_for("public.user", username=a_user.username, _external=True)
    for a in User.query.find_by(username=username).limit(10):
        activities.push(
            {
              "@context": "https://www.w3.org/ns/activitystreams",
              "type": "Create",
              "id": a.id,
              "actor": url_user,
              "object": {
                "id": a.url,
                "type": "Note",
                "attributedTo": url_user,
                "content": a.text,
              },
              "published": a.date,
              "to": [url_user],
            }
        )
    apub = {
      "@context": "https://www.w3.org/ns/activitystreams",
      "summary": username + ' - dribs',
      "type": "OrderedCollection",
      "orderedItems": activities,
      "totalItems": len(activities),
    }
    resp = Response(jsonify(apub))
    resp.headers['Content-Type'] = 'application/activity+json'
    return resp
    