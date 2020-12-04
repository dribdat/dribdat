# -*- coding: utf-8 -*-
"""The user module."""
from . import views, validators  # noqa

from .constants import (
    USER_ROLE, ADMIN, USER, USER_STATUS, ACTIVE,
    projectProgressList, getProjectPhase,
    resourceTypeList, getResourceType,
)
