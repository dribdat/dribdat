# -*- coding: utf-8 -*-
from wtforms.validators import DataRequired, ValidationError

class UniqueValidator(object):
    """Validator that checks field uniqueness"""
    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'The %s must be unique.' % field
        self.message = message
    def __call__(self, form, field):
        existing = self.model.query.filter(getattr(self.model, self.field) == field.data).first()
        if existing:
            curid = form.id.data
            if not curid or int(curid) != int(existing.id):
                raise ValidationError(self.message)
