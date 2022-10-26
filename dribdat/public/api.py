# -*- coding: utf-8 -*-
"""API calls for dribdat."""
import boto3
from flask import (
    Blueprint, current_app,
    Response, request, redirect,
    stream_with_context, send_file,
    jsonify, flash, url_for, escape
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from ..extensions import db
from ..utils import timesince, random_password
from ..decorators import admin_required
from ..user.models import Event, Project, Activity
from ..aggregation import GetProjectData, AddProjectData, GetEventUsers
from ..apipackage import ImportEventPackage, PackageEvent
from ..apiutils import (
    get_project_list,
    get_event_activities,
    get_schema_for_user_projects,
    expand_project_urls,
    gen_csv,
)
import tempfile
import json
from os import path

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
        + event_name + '_dribdat.csv'
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


@blueprint.route('/event/current/categories.json')
def categories_list_current_json():
    """Output JSON of categories in the current event."""
    event = Event.query.filter_by(is_current=True).first()
    categories = [c.data for c in event.categories_for_event()]
    return jsonify(categories=categories, event=event.data)

# ------ ACTIVITY FEEDS ---------


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


@blueprint.route('/project/<int:project_id>/activity.json')
def project_activity_json(project_id):
    """Output JSON of recent activity of a project."""
    limit = request.args.get('limit') or 10
    project = Project.query.filter_by(id=project_id).first_or_404()
    query = Activity.query.filter_by(project_id=project.id).order_by(
        Activity.id.desc()).limit(limit).all()
    activities = [a.data for a in query]
    return jsonify(project=project.data, activities=activities)


@blueprint.route('/project/<int:project_id>/info.json')
def project_info_json(project_id):
    """Output JSON info for a specific project."""
    project = Project.query.filter_by(id=project_id).first_or_404()
    activities = []
    for user in project.get_team():
        activities.append({
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
        'creator': {
            'id': project.user.id,
            'username': project.user.username
        },
        'team': activities
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


@blueprint.route('/event/load/datapackage', methods=["GET", "POST"])
@admin_required
def event_load_datapackage():  # noqa: C901
    """Load event data from URL."""
    url = request.args.get('url')
    filedata = request.files['file']
    if filedata and request.form.get('import'):
        url = filedata.filename
        import_level = request.form.get('import')
    else:
        import_level = request.args.get('import')
    # Check link
    if not url or 'datapackage.json' not in url:
        return jsonify(status='Error', errors=['Missing datapackage.json url'])
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
    if filedata and filedata.filename != '':
        results = prepare_datapackage(filedata, dry_run, all_data)
        event_names = ', '.join([r['name'] for r in results['events']])
        if 'errors' in results:
            return jsonify(status='Error', errors=results['errors'])
        else:
            flash("Events uploaded: %s" % event_names, 'success')
            return redirect(url_for("admin.events"))
    return jsonify(status=status, results=results)


def prepare_datapackage(filedata, dry_run, all_data):
    """Saves a temporary file and provides details."""
    ext = filedata.filename.split('.')[-1].lower()
    if ext not in ['json']:
        return {'errors': ['Invalid format (allowed: JSON)']}
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = path.join(tmpdir, secure_filename(filedata.filename))
        filedata.save(filepath)
        try:
            with open(filepath, mode='rb') as file:
                data = json.load(file)
            return ImportEventPackage(data, dry_run, all_data)
        except json.decoder.JSONDecodeError:
            return {'errors': ['Could not load package due to JSON error']}


@blueprint.route('/event/push/datapackage', methods=["PUT", "POST"])
def event_push_datapackage():
    """Upload event data from a Data Package."""
    key = request.headers.get('key')
    if not key or key != current_app.config['SECRET_API']:
        return jsonify(status='Error', errors=['Invalid API key'])
    data = request.get_json(force=True)
    results = ImportEventPackage(data)
    if 'errors' in results:
        return jsonify(status='Error', errors=results['errors'])
    return jsonify(status='Complete', results=results)


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
    project.update()
    db.session.add(project)
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
        project = AddProjectData(project)
    return project


# ------ FRONTEND -------


@blueprint.route('/project/autofill', methods=['GET', 'POST'])
@login_required
def project_autofill():
    """Routine used to help sync project data."""
    url = request.args.get('url')
    data = GetProjectData(url)
    return jsonify(data)

# ------ UPLOADING -------

# TODO: move to separate upload.py ?


ACCEPTED_TYPES = [
    'png', 'jpg', 'jpeg', 'gif',  # ʕ·͡ᴥ·ʔ
    'json', 'geojson',            # ( ͡° ͜ʖ ͡°)
    'csv', 'tsv',                 # ¯\_(ツ)_/¯
    'ods', 'pdf',                # (ノಠ ∩ಠ)ノ彡
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
    else:
        s3_obj = boto3.client(
            service_name='s3',
            region_name=current_app.config['S3_REGION'],
            aws_access_key_id=current_app.config['S3_KEY'],
            aws_secret_access_key=current_app.config['S3_SECRET'],
        )
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
    package = PackageEvent(event, current_user, host_url, full_contents)
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
def package_current_event(format):
    """Download a Data Package for an event."""
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    return generate_event_package(event, format)


@blueprint.route('/event/<int:event_id>/datapackage.<format>', methods=["GET"])
def package_specific_event(event_id, format):
    """Download a Data Package for an event."""
    event = Event.query.filter_by(id=event_id).first_or_404()
    return generate_event_package(event, format)


# ------ USER API --------


@blueprint.route('/user/current/my-hackathons.json')
def current_user_hackathon_json():
    """Output JSON-LD about a User's Event according to schema."""
    """See https://schema.org/Hackathon."""
    host_url = request.host_url
    data = get_schema_for_user_projects(current_user, host_url)
    return jsonify(data)
