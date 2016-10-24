# -*- coding: utf-8 -*-

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

# Project progress
PR_NEW = 0
PR_RESEARCHED = 10
PR_SKETCHED = 20
PR_PROTOTYPED = 30
PR_LAUNCHED = 40
PR_LIVE = 50
PROJECT_PROGRESS = {
    PR_NEW:         'A team has formed and announced the project',
    PR_RESEARCHED:  'Research has been done to define the scope',
    PR_SKETCHED:    'Initial designs have been sketched and shared',
    PR_PROTOTYPED:  'A prototype of the idea has been developed',
    PR_LAUNCHED:    'The prototype has been launched and shared',
    PR_LIVE:        'This project is now live and publicly available',
}
PROJECT_PROGRESS_PHASE = {
    PR_NEW:         'Researching',
    PR_RESEARCHED:  'Sketching',
    PR_SKETCHED:    'Prototyping',
    PR_PROTOTYPED:  'Launching',
    PR_LAUNCHED:    'Promoting',
    PR_LIVE:        'Supporting',
}
def projectProgressList():
    pl = [(g, PROJECT_PROGRESS[g]) for g in PROJECT_PROGRESS]
    return sorted(pl, key=lambda x: x[0])
