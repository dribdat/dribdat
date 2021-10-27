# -*- coding: utf-8 -*-

import boto3
from frictionless import Package, Resource
from flask import (
    Blueprint, current_app,
    Response, request,
    stream_with_context, send_file,
    jsonify,
)
from flask_login import login_required, current_user

from sqlalchemy import or_

from ..extensions import db
from ..utils import timesince, random_password, format_date
from ..decorators import admin_required

from ..user.models import Event, Project, Activity
from ..aggregation import GetProjectData, AddProjectData, GetEventUsers
from ..apipackage import ImportEventPackage, ImportEventByURL
from ..apiutils import (
    get_projects_by_event, get_project_summaries,
    get_event_users, get_event_activities,
    get_event_categories,
    expand_project_urls,
    gen_csv,
)

from datetime import datetime
import tempfile

blueprint = Blueprint('api', __name__, url_prefix='/api')


# ------ EVENT INFORMATION ---------

@blueprint.route('/event/current/info.json')
def info_current_event_json():
    """ API: Outputs JSON about the current event """
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    timeuntil = timesince(event.countdown, until=True)
    return jsonify(event=event.data, timeuntil=timeuntil)


@blueprint.route('/event/<int:event_id>/info.json')
def info_event_json(event_id):
    """ API: Outputs JSON about an event """
    event = Event.query.filter_by(id=event_id).first_or_404()
    timeuntil = timesince(event.countdown, until=True)
    return jsonify(event=event.data, timeuntil=timeuntil)


@blueprint.route('/event/<int:event_id>/hackathon.json')
def info_event_hackathon_json(event_id):
    """ API: Outputs JSON-LD about an Event according to schema """
    """ See https://schema.org/Hackathon """
    event = Event.query.filter_by(id=event_id).first_or_404()
    return jsonify(event.get_schema(request.host_url))

# ------ EVENT PROJECTS ---------


def project_list(event_id, full_data=False):
    """ Collect all projects and challenges for an event """
    is_moar = bool(request.args.get('moar', type=bool)) or full_data
    projects = get_projects_by_event(event_id)
    host_url = request.host_url
    return get_project_summaries(projects, host_url, is_moar)


@blueprint.route('/event/current/projects.json')
def project_list_current_json():
    """ API: Outputs JSON of projects in the current event with its info """
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    return jsonify(projects=project_list(event.id), event=event.data)


@blueprint.route('/event/<int:event_id>/projects.json')
def project_list_json(event_id):
    """ API: Outputs JSON of all projects at a specific event """
    return jsonify(projects=project_list(event_id))


def project_list_csv(event_id, event_name):
    headers = {
        'Content-Disposition': 'attachment; filename='
        + event_name + '_dribdat.csv'
    }
    return Response(stream_with_context(gen_csv(project_list(event_id))),
                    mimetype='text/csv',
                    headers=headers)


@blueprint.route('/event/<int:event_id>/projects.csv')
def project_list_event_csv(event_id):
    """ API: Outputs CSV of all projects in an event """
    event = Event.query.filter_by(id=event_id).first_or_404()
    return project_list_csv(event.id, event.name)


@blueprint.route('/event/current/projects.csv')
def project_list_current_csv():
    """ API: Outputs CSV of projects and challenges in the current event """
    event = Event.query.filter_by(is_current=True).first() or \
        Event.query.order_by(Event.id.desc()).first_or_404()
    return project_list_csv(event.id, event.name)


@blueprint.route('/event/current/categories.json')
def categories_list_current_json():
    """ API: Outputs JSON of categories in the current event """
    event = Event.query.filter_by(is_current=True).first()
    categories = [c.data for c in event.categories_for_event()]
    return jsonify(categories=categories, event=event.data)

# ------ ACTIVITY FEEDS ---------


@blueprint.route('/event/<int:event_id>/activity.json')
def event_activity_json(event_id):
    """ API: Outputs JSON of recent activity in an event """
    limit = request.args.get('limit') or 50
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    return jsonify(activities=get_event_activities(event_id, limit, q))


@blueprint.route('/event/current/activity.json')
def event_activity_current_json():
    """ API: Outputs JSON of categories in the current event """
    event = Event.query.filter_by(is_current=True).first()
    if not event:
        return jsonify(activities=[])
    return event_activity_json(event.id)


@blueprint.route('/event/<int:event_id>/activity.csv')
def event_activity_csv(event_id):
    """ API: Outputs CSV of an event activity """
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
    """ API: Outputs JSON of recent activity across all projects """
    limit = request.args.get('limit') or 10
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    return jsonify(activities=get_event_activities(None, limit, q))


@blueprint.route('/project/posts.json')
def projects_posts_json():
    """ API: Outputs JSON of recent posts (activity) across projects """
    limit = request.args.get('limit') or 10
    q = request.args.get('q') or None
    if q and len(q) < 3:
        q = None
    return jsonify(activities=get_event_activities(None, limit, q, "post"))


@blueprint.route('/project/<int:project_id>/activity.json')
def project_activity_json(project_id):
    """ API: Outputs JSON of recent activity of a project """
    limit = request.args.get('limit') or 10
    project = Project.query.filter_by(id=project_id).first_or_404()
    query = Activity.query.filter_by(project_id=project.id).order_by(
        Activity.id.desc()).limit(limit).all()
    activities = [a.data for a in query]
    return jsonify(project=project.data, activities=activities)


@blueprint.route('/project/<int:project_id>/info.json')
def project_info_json(project_id):
    """ API: Outputs JSON info for a specific project """
    project = Project.query.filter_by(id=project_id).first_or_404()
    activities = []
    for user in project.team():
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
    """ API: Full text search projects """
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


@blueprint.route('/event/load/datapackage', methods=["GET"])
@admin_required
def event_load_datapackage():
    """ API: Loads event data from URL """
    url = request.args.get('url')
    if not url or 'datapackage.json' not in url:
        return jsonify(status='Error', errors=['Missing datapackage.json url'])
    dry_run = True
    all_data = False
    status = "Preview"
    import_level = request.args.get('import')
    if import_level == 'basic':
        dry_run = False
        status = "Basic"
    if import_level == 'full':
        dry_run = False
        all_data = True
        status = "Complete"
    results = ImportEventByURL(url, dry_run, all_data)
    if 'errors' in results:
        return jsonify(status='Error', errors=results['errors'])
    return jsonify(status=status, results=results)


@blueprint.route('/event/push/datapackage', methods=["PUT", "POST"])
def event_push_datapackage():
    """ API: Pushes event data """
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
    """ API: Pushes data into a project """
    data = request.get_json(force=True)
    if 'key' not in data or data['key'] != current_app.config['SECRET_API']:
        return jsonify(error='Invalid key')
    project = Project.query.filter_by(hashtag=data['hashtag']).first()
    if not project:
        project = Project()
        project.user_id = 1
        project.progress = 0
        # project.autotext_url = "#bot"
        # project.is_autoupdate = True
        project.event = Event.query.filter_by(is_current=True).first()
    elif project.user_id != 1 or project.is_hidden:
        return jsonify(error='Access denied')
    project.hashtag = data['hashtag']
    if 'name' in data and len(data['name']) > 0:
        project.name = data['name']
    else:
        project.name = project.hashtag.replace('-', ' ')
    if 'summary' in data and len(data['summary']) > 0:
        project.summary = data['summary']
    hasLongtext = 'longtext' in data and len(data['longtext']) > 0
    if hasLongtext:
        project.longtext = data['longtext']
    if 'autotext_url' in data and data['autotext_url'].startswith('http'):
        project.autotext_url = data['autotext_url']
        if not project.source_url or project.source_url == '':
            project.source_url = data['autotext_url']
    # MAX progress
    if 'levelup' in data and 0 < project.progress + data['levelup'] * 10 < 50:
        project.progress = project.progress + data['levelup'] * 10
    # return jsonify(data=data)
    if project.autotext_url is not None and not hasLongtext:
        # Now try to autosync
        project = AddProjectData(project)
    project.update()
    db.session.add(project)
    db.session.commit()
    return jsonify(success='Updated', project=project.data)

# ------ FRONTEND -------


@blueprint.route('/project/autofill', methods=['GET', 'POST'])
@login_required
def project_autofill():
    """ API routine used to help sync project data """
    url = request.args.get('url')
    data = GetProjectData(url)
    return jsonify(data)


# TODO: move to separate upload.py ?

ACCEPTED_TYPES = ['png', 'jpg', 'jpeg', 'gif', 'json']


@blueprint.route('/project/uploader', methods=["POST"])
@login_required
def project_uploader():
    """ API: Enables uploading images and files into a project """
    if not current_app.config['S3_KEY']:
        return ''
    if len(request.files) == 0:
        return 'No files selected'
    img = request.files['file']
    if not img or img.filename == '':
        return 'No filename'
    ext = img.filename.split('.')[-1].lower()
    if ext not in ACCEPTED_TYPES:
        return 'Invalid format'
    filename = random_password(24) + '.' + ext
    # with tempfile.TemporaryDirectory() as tmpdir:
    # img.save(path.join(tmpdir, filename))
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
    return '/'.join([current_app.config['S3_HTTPS'], s3_filepath])


# TODO: move to packager.py ?


@blueprint.route('/event/current/datapackage.<format>', methods=["GET"])
@login_required
def package_current_event(format):
    event = Event.query.filter_by(is_current=True).first() or \
            Event.query.order_by(Event.id.desc()).first_or_404()
    return package_event(event, format)


@blueprint.route('/event/<int:event_id>/datapackage.<format>', methods=["GET"])
@login_required
def package_specific_event(event_id, format):
    event = Event.query.filter_by(id=event_id).first_or_404()
    return package_event(event, format)


def package_event(event, format):
    if format not in ['zip', 'json']:
        return "Format not supported"
    # Set up a data package
    package = Package(
        name='event-%d' % event.id,
        title=event.name,
        description="Event and project details collected with dribdat",
        keywords=["dribdat", "hackathon", "co-creation"],
        sources=[{
            "title": "dribdat", "path": "https://dribdat.cc"
        }],
        licenses=[{
            "name": "ODC-PDDL-1.0",
            "path": "http://opendatacommons.org/licenses/pddl/",
            "title": "Open Data Commons Public Domain Dedication & License 1.0"
        }],
        contributors=[{
            "title": current_user.username,
            "path": current_user.webpage_url or '',
            "role": "author"
        }],
        homepage=request.host_url,
        created=format_date(datetime.now(), '%Y-%m-%dT%H:%M'),
        version="0.1.0",
    )

    # if False:  # as CSV
    #     fp_projects = tempfile.NamedTemporaryFile(
    #         mode='w+t', prefix='projects-', suffix='.csv')
    #     # print("Writing to temp CSV file", fp_projects.name)
    #     fp_projects.write(gen_csv(project_list(event.id)))
    #     resource = Resource(fp_projects.name)
    # if False:
    #     # print("Generating in-memory rowset")
    #     project_rows = gen_rows(project_list(event.id))
    #     resource = Resource(
    #         name='projects',
    #         data=project_rows,
    #     )

    # Generate resources
    # print("Generating in-memory JSON of event")
    package.add_resource(Resource(
            name='events',
            data=[event.get_full_data()],
        ))
    # print("Generating in-memory JSON of projects")
    package.add_resource(Resource(
            name='projects',
            data=project_list(event.id, True),
        ))
    if format == 'zip':
        # print("Generating in-memory JSON of participants")
        package.add_resource(Resource(
                name='users',
                data=get_event_users(event),
            ))
        # print("Generating in-memory JSON of activities")
        package.add_resource(Resource(
                name='activities',
                data=get_event_activities(event.id, 500),
            ))
        # print("Generating in-memory JSON of activities")
        package.add_resource(Resource(
                name='categories',
                data=get_event_categories(event.id),
            ))
        # print("Adding supplementary README")
        package.add_resource(Resource(
                name='readme',
                path='PACKAGE.txt',
            ))

    # Generate data package
    fp_package = tempfile.NamedTemporaryFile(
        prefix='datapackage-', suffix='.zip')
    # print("Saving at", fp_package.name)
    if format == 'json':
        return jsonify(package)
    elif format == 'zip':
        package.to_zip(fp_package.name)
        return send_file(fp_package.name, as_attachment=True)
