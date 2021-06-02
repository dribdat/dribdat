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

# Project progress stages
project_stages = load_csv_presets('stages', 'name')
PR_CHALLENGE = int(project_stages['CHALLENGE']['id'])
PROJECT_PROGRESS = {}
PROJECT_PROGRESS_PHASE = {}
for ps in project_stages:
    pid = int(project_stages[ps]['id'])
    PROJECT_PROGRESS[pid] = project_stages[ps]['description']
    PROJECT_PROGRESS_PHASE[pid] = project_stages[ps]['phase']

def projectProgressList(All=True, WithEmpty=True):
    if not All:
        return [(PR_CHALLENGE, PROJECT_PROGRESS[PR_CHALLENGE])]
    pl = [(g, PROJECT_PROGRESS[g]) for g in PROJECT_PROGRESS]
    if WithEmpty:
        pl.append((-100, ''))
    return sorted(pl, key=lambda x: x[0])

def getProjectPhase(project):
    if project is None or project.progress is None:
        return ""
    if not project.progress in PROJECT_PROGRESS_PHASE:
        return PROJECT_PROGRESS_PHASE[PR_CHALLENGE]
    return PROJECT_PROGRESS_PHASE[project.progress]

def isUserActive(user):
    if not user or not 'active' in user.__dir__():
        return False
    return user.active
