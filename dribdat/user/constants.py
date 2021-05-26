# -*- coding: utf-8 -*-

from ..utils import load_csv_presets

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

# Linked resources
RESOURCE_CODES = {
    'data': 100,
    'code': 200,
    'tool': 300,
    'other': 0
}
RESOURCE_TYPES = {
    RESOURCE_CODES['data']: "Data",
    # 'data/geodata': "Geodata",
    # 'data/thingspeak': "Sensor data",
    # 'data/hdf5': "Deep learning model",
    RESOURCE_CODES['code']: "Code",
    # 'code/sparql': "Query code",
    # 'code/framework': "Code framework",
    # 'code/lib': "Programming library",
    RESOURCE_CODES['tool']: "Tool",
    # 'tool/kanban': "Project planner",
    # 'tool/sim': "Simulation tool",
    # 'tool/ux': "Wireframing app",
    RESOURCE_CODES['other']: "Other",
}

# Project progress stages
project_stages = load_csv_presets('stages', 'name')
PR_CHALLENGE = int(project_stages['CHALLENGE']['id'])
PROJECT_PROGRESS = {}
PROJECT_PROGRESS_PHASE = {}
for ps in project_stages:
    pid = int(project_stages[ps]['id'])
    PROJECT_PROGRESS[pid] = project_stages[ps]['description']
    PROJECT_PROGRESS_PHASE[pid] = project_stages[ps]['phase']

def resourceTypeList():
    pl = [(g, RESOURCE_TYPES[g]) for g in RESOURCE_TYPES]
    return sorted(pl, key=lambda x: x[0])

def getResourceType(resource):
    if resource is None: return ""
    if resource.type_id is None: return RESOURCE_TYPES[0]
    if not resource.type_id in RESOURCE_TYPES: return ""
    return RESOURCE_TYPES[resource.type_id]

def projectProgressList(All=True, WithEmpty=True):
    if not All:
        return [(PR_CHALLENGE, PROJECT_PROGRESS[PR_CHALLENGE])]
    pl = [(g, PROJECT_PROGRESS[g]) for g in PROJECT_PROGRESS]
    if WithEmpty:
        pl.append((-100, ''))
    return sorted(pl, key=lambda x: x[0])

def getProjectPhase(project):
    if project is None or project.progress is None: return ""
    if not project.progress in PROJECT_PROGRESS_PHASE: return ""
    return PROJECT_PROGRESS_PHASE[project.progress]

def isUserActive(user):
    if not user or not 'active' in user.__dir__():
        return False
    return user.active
