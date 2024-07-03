# -*- coding: utf-8 -*-
"""OpenAPI documentation for dribdat."""
import marshmallow as ma

from flask import (
    current_app,
    #Blueprint, 
    #Response, request, redirect,
    #stream_with_context, send_file,
    #jsonify, flash, url_for
)
from ..user.models import Event, Project, Activity, User
from flask_smorest import Api, Blueprint, abort

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

class EventSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        include_fk = True
        load_instance = True


app.config["API_TITLE"] = "dribdat API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
api = Api(current_app)

blueprint = Blueprint('openapi', __name__, url_prefix='/openapi', description='OpenAPI specification for dribdat')

class EventQueryArgsSchema(ma.Schema):
    name = ma.fields.String()

@blueprint.route('/')
class Events(MethodView):
    @blp.arguments(EventQueryArgsSchema, location="query")
    @blp.response(200, EventSchema(many=True))
    def get(self, args):
        """List events"""
        return Event.get(filters=args)
