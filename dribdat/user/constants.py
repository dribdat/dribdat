# -*- coding: utf-8 -*-
"""Constants for user functions."""
from os import environ as os_env
from ..utils import load_yaml_presets
from ..apifetch import FetchStageConfig

# User role
USER = 0
ADMIN = 1
USER_ROLE = {
    ADMIN: 'admin',
    USER: 'user',
}

# User status
INACTIVE = 0
ACTIVE = 1
USER_STATUS = {
    INACTIVE: 'inactive',
    ACTIVE: 'active',
}
CLEAR_STATUS_AFTER = 10 # minutes

# Resource types
RESOURCE_TYPES = {
    0: ('forks', "Forks the source of"),
    1: ('proves', "Demo or example of"),
    2: ('permits', "License or terms applied"),
    3: ('includes', "Includes this library or resource"),
    4: ('uses data', "Uses this data source"),
    5: ('built with', "Uses this hardware component"),
    6: ('inspired by', "Is inspired by this"),
}

# Content length
MAX_EXCERPT_LENGTH = 500

PR_CHALLENGE = 0
PR_STAGES = { 'PROGRESS': {}, 'STAGE': {} }


def resourceTypeList(verbose=False):
    """Get a sorted list of resources by type."""
    # TODO: clean up
    vb = 1 if verbose else 0
    pl = [(g, RESOURCE_TYPES[g][vb]) for g in RESOURCE_TYPES]
    return sorted(pl, key=lambda x: x[0])


def getResourceType(resource, verbose=False):
    """Return a resource type."""
    vb = 1 if verbose else 0
    # TODO: clean up
    if resource is None:
        return ""
    if resource.type_id is None:
        return RESOURCE_TYPES[0][vb]
    if resource.type_id not in RESOURCE_TYPES:
        return ""
    return RESOURCE_TYPES[resource.type_id][vb]


def load_project_stages():
    """Initialize progress stages from file."""
    if not PR_STAGES['PROGRESS'] == {}: return
    DRIBDAT_STAGE = os_env.get('DRIBDAT_STAGE', None)
    if DRIBDAT_STAGE:
        project_stages = FetchStageConfig(DRIBDAT_STAGE)
    else:
        project_stages = load_yaml_presets('stages', 'name')
    for ps in project_stages:
        pid = int(project_stages[ps]['id'])
        PR_STAGES['PROGRESS'][pid] = project_stages[ps]['description']
        PR_STAGES['STAGE'][pid] = project_stages[ps]


def projectProgressList(All=True, WithEmpty=True):
    """Return sorted progress list."""
    if not All:
        return [(PR_CHALLENGE, PR_STAGES['PROGRESS'][PR_CHALLENGE])]
    all_stages = PR_STAGES['PROGRESS']
    pl = [(g, PR_STAGES['STAGE'][g]['name'] + all_stages[g]) for g in all_stages]
    if WithEmpty:
        pl.append((-100, ''))
    return sorted(pl, key=lambda x: x[0])


def stageProjectToNext(project):
    """Updates project stage to next level."""
    if project.progress < 0:
        # Approve a challenge
        project.progress = projectProgressList(False, False)[0][0]
        return True
    found_next = False
    # Promote to next stage in progress list
    for a in projectProgressList(True, False):
        if found_next:
            project.progress = a[0]
            break
        if a[0] == project.progress or \
            not project.progress:
            found_next = True
    return found_next
    

def getProjectStages():
    """Return sorted stages list."""
    pl = []
    for ix, g in enumerate(sorted(PR_STAGES['PROGRESS'])):
        stage = PR_STAGES['STAGE'][g]
        stage['index'] = ix + 1
        pl.append(stage)
    return pl


def getStageByProgress(progress):
    """Return progress detail for a progress level."""
    if progress is None:
        return None
    if progress not in PR_STAGES['STAGE']:
        if PR_CHALLENGE in PR_STAGES['STAGE']:
            return PR_STAGES['STAGE'][PR_CHALLENGE]
        else:
            return None
    return PR_STAGES['STAGE'][progress]


def getProjectPhase(project):
    """Return progress phase for a project."""
    if project is None or project.progress is None:
        return ""
    stage = getStageByProgress(project.progress)
    if stage is None:
        return ""
    return stage['phase']


def isUserActive(user):
    """Check if a user is active."""
    if not user or 'active' not in user.__dir__():
        return False
    return user.active


def validateProjectData(project):
    """Validate the stage of a project."""
    stage = project.stage
    all_valid = True
    # Collect project data
    project_data = project.data
    # Iterate through the stage conditions
    for v in stage['conditions']['validate']:
        v['valid'] = False
        vf = v['field']
        if vf in project_data:
            pdvf = project_data[vf]
            if (
                ('min' in v and len(pdvf) >= v['min'])
                or ('max' in v and v['min'] <= len(pdvf) <= v['max'])
                or (
                    'test' in v and v['test'] == 'validurl'
                    and pdvf.startswith('http')
                )
            ):
                v['valid'] = True
        if not v['valid']:
            all_valid = False
    return stage, all_valid


def getActivityByType(a, only_active=True):  # noqa: C901
    """Return Activity item representated as a tuple."""
    author = title = text = icon = None
    # Obtain author if available
    if a.user:
        author = a.user.username
        if only_active and not a.user.active:
            return None
    else:
        author = "?"

    # We could use a config data structure like this:
    # {
    #     'sync': {
    #         'text': 'Repository updated',
    #         'icon': 'code'
    #     },
    #     'post': {
    #         'icon': 'comment'
    #     },
    #     'star': {
    #         'text': 'Joined the team',
    #         'icon': 'thumbs-up'
    #     },
    #     'update': {
    #         'author': None,
    #         'icon': 'random'
    #     }
    # }

    # Based on action, populate activity fields
    if a.action == 'sync':
        text = "Repository updated"
        icon = 'code'
    elif a.action == 'post' and a.name == 'review':
        text = a.content
        icon = 'comment'
    elif a.action == 'post' and a.content is not None:
        text = a.content
        icon = 'pencil'
    elif a.name == 'star':
        # title = "Team forming"
        text = "Joined the team"
        icon = 'thumbs-up'
    elif a.name == 'update' and a.action == 'commit':
        # title = "Code commit"
        text = a.content
        author = None
        icon = 'random'
    elif a.name == 'revert':
        text = "Reverted to"
        if a.project_version:
            text += " version %d" % a.project_version
        icon = 'paperclip'
    elif a.name == 'update':
        text = "Edited"
        if a.project_version:
            text += " (version %d)" % a.project_version
        icon = 'paperclip'
    # elif a.name == 'revert':
    #     text = "Reverted content"
    #     if a.project_version:
    #         text += " version %d" % a.project_version
    #     icon = 'undo'
    elif a.name == 'create':
        text = "First post <a class='btn btn-light float-right' href='/%s/challenge'>View challenge</a>" % a.project.url
        icon = 'flag-checkered'
    elif a.name == 'boost':
        title = a.action
        text = a.content
        icon = 'trophy'
    else:
        return None
    return (author, title, text, icon)


# TODO: make this happen in app.py
load_project_stages()
