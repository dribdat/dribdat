# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, make_response, request, flash, jsonify
from flask.ext.login import login_required, current_user

from ..extensions import db
from ..decorators import admin_required

from ..user.models import User
from .forms import UserForm

import json

blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@blueprint.route('/')
@login_required
@admin_required
def index():
    users = User.query.all()
    return render_template('admin/index.html', users=users, active='index')


@blueprint.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users, active='users')


@blueprint.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = UserForm(obj=user, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        flash('User updated.', 'success')

    return render_template('admin/user.html', user=user, form=form)

@blueprint.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    user = User()
    form = UserForm(obj=user, next=request.args.get('next'))

    if form.validate_on_submit():
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        flash('User added.', 'success')

    return render_template('admin/usernew.html', form=form)
