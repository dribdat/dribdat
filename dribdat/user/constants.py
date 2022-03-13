# -*- coding: utf-8 -*-

from ..utils import load_yaml_presets

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


# TODO: clean up
def resourceTypeList(verbose=False):
    vb = 1 if verbose else 0
    pl = [(g, RESOURCE_TYPES[g][vb]) for g in RESOURCE_TYPES]
    return sorted(pl, key=lambda x: x[0])


# TODO: clean up
def getResourceType(resource, verbose=False):
    vb = 1 if verbose else 0
    if resource is None:
        return ""
    if resource.type_id is None:
        return RESOURCE_TYPES[0][vb]
    if resource.type_id not in RESOURCE_TYPES:
        return ""
    return RESOURCE_TYPES[resource.type_id][vb]


# Project progress stages
project_stages = load_yaml_presets('stages', 'name')
PR_CHALLENGE = int(project_stages['CHALLENGE']['id'])
PROJECT_PROGRESS = {}
PROJECT_PROGRESS_STAGE = {}
for ps in project_stages:
    pid = int(project_stages[ps]['id'])
    PROJECT_PROGRESS[pid] = project_stages[ps]['description']
    PROJECT_PROGRESS_STAGE[pid] = project_stages[ps]


def projectProgressList(All=True, WithEmpty=True):
    if not All:
        return [(PR_CHALLENGE, PROJECT_PROGRESS[PR_CHALLENGE])]
    pl = [(g, PROJECT_PROGRESS[g]) for g in PROJECT_PROGRESS]
    if WithEmpty:
        pl.append((-100, ''))
    return sorted(pl, key=lambda x: x[0])


def getProjectStages():
    pl = []
    for ix, g in enumerate(sorted(PROJECT_PROGRESS)):
        stage = PROJECT_PROGRESS_STAGE[g]
        stage['index'] = ix + 1
        pl.append(stage)
    return pl


def getProjectPhase(project):
    if project is None or project.progress is None:
        return ""
    if project.progress not in PROJECT_PROGRESS_STAGE:
        return PROJECT_PROGRESS_STAGE[PR_CHALLENGE]['phase']
    return PROJECT_PROGRESS_STAGE[project.progress]['phase']


def getStageByProgress(progress):
    if progress is None:
        return None
    if progress not in PROJECT_PROGRESS_STAGE:
        return PROJECT_PROGRESS_STAGE[PR_CHALLENGE]
    return PROJECT_PROGRESS_STAGE[progress]


def isUserActive(user):
    if not user or 'active' not in user.__dir__():
        return False
    return user.active


def validateProjectData(project):
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


def getActivityByType(a, only_active=True):
    """ Returns Activity item representated as a tuple """
    author = title = text = icon = None
    # Obtain author if available
    if a.user:
        author = a.user.username
        if only_active and not a.user.active:
            return None
    else:
        author = "?"
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
    elif a.name == 'update':
        text = "Edited content"
        if a.project_version:
            text += " version %d" % a.project_version
        icon = 'paperclip'
    elif a.name == 'create':
        text = "Challenge posted"
        icon = 'flag-checkered'
    elif a.name == 'boost':
        title = a.action
        text = a.content
        icon = 'trophy'
    else:
        return None
    return (author, title, text, icon)
