# -*- coding: utf-8 -*-
from wtforms import ValidationError


class UniqueValidator(object):
    """Validator that checks field uniqueness"""

    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'The %s must be unique.' % field
        self.message = message

    def __call__(self, form, field):
        existing = self.model.query.filter(
            getattr(self.model, self.field) == field.data).first()
        if existing:
            curid = form.id.data
            if not curid or int(curid) != int(existing.id):
                raise ValidationError(self.message)


def event_date_check(form, starts_date):
    ends_date = form.ends_date.data
    if starts_date.data > ends_date:
        raise ValidationError('Start date must not be after end date.')


def event_time_check(form, starts_time):
    ends_time = form.ends_time.data
    ends_date = form.ends_date.data
    starts_date = form.starts_date.data
    if starts_date == ends_date and starts_time.data > ends_time:
        raise ValidationError('Start time must be before end time.')
