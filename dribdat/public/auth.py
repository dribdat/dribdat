# -*- coding: utf-8 -*-
"""Authentication views."""

from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app, jsonify)

from flask_login import login_user, logout_user, login_required, current_user

from dribdat.user.models import User, Event, Role
from dribdat.extensions import login_manager
from dribdat.utils import flash_errors, random_password, sanitize_input
from dribdat.public.forms import LoginForm, UserForm
from dribdat.user.forms import RegisterForm
from dribdat.database import db

from flask_dance.contrib.slack import slack

blueprint = Blueprint('auth', __name__, static_folder="../static")

def current_event():
    return Event.query.filter_by(is_current=True).first()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

def slack_enabled():
    """Check if Slack has been configured"""
    dsi = current_app.config["OAUTH_TYPE"] and current_app.config["OAUTH_TYPE"].lower() == 'slack'
    return dsi is not None and dsi != ""


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user, remember=True)
            flash("You are logged in.", 'success')
            redirect_url = request.args.get("next") or url_for("public.home")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/login.html", current_event=current_event(), form=form, slack_enabled=slack_enabled())


@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if request.args.get('name') and not form.username.data:
        form.username.data = request.args.get('name')
    if request.args.get('email') and not form.email.data:
        form.email.data = request.args.get('email')
    if request.args.get('web') and not form.webpage_url.data:
        form.webpage_url.data = request.args.get('web')
    user1 = User.query.filter_by(email=form.email.data).first()
    if user1:
        flash("A user account with this email already exists", 'warning')
    elif form.validate_on_submit():
        new_user = User.create(
                        username=sanitize_input(form.username.data),
                        email=form.email.data,
                        webpage_url=form.webpage_url.data,
                        password=form.password.data,
                        active=True)
        new_user.socialize()
        if User.query.count() == 1:
            new_user.is_admin = True
            new_user.save()
            flash("Administrative user created - have fun!", 'success')
        else:
            flash("Thank you for registering. You can now log in and submit projects.", 'success')
        login_user(new_user, remember=True)
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    return render_template('public/register.html', current_event=current_event(), form=form, slack_enabled=slack_enabled())


@blueprint.route('/logout/')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route('/forgot/')
def forgot():
    """Forgot password."""
    return render_template('public/forgot.html', current_event=current_event(), slack_enabled=slack_enabled())


@blueprint.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    user = current_user
    form = UserForm(obj=user, next=request.args.get('next'))
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by('name')]

    if form.validate_on_submit():
        # Assign roles
        user.roles = [Role.query.filter_by(id=r).first() for r in form.roles.data]
        del form.roles

        # Sanitize username
        user.username = sanitize_input(form.username.data)
        del form.username

        # Assign password if changed
        originalhash = user.password
        form.populate_obj(user)
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.password = originalhash

        db.session.add(user)
        db.session.commit()
        user.socialize()
        flash('Profile updated.', 'success')
        return redirect(url_for('public.user', username=user.username))

    if not form.roles.choices:
        del form.roles
    else:
        form.roles.data = [(r.id) for r in user.roles]
    return render_template('public/useredit.html', user=user, form=form, active='profile')


@blueprint.route("/slack_login", methods=["GET", "POST"])
def slack_login():
    if not slack.authorized:
        flash('Access denied to Slack', 'error')
        return redirect(url_for("auth.login"))

    resp = slack.get("https://slack.com/api/users.identity")
    if not resp.ok:
        flash('Unable to access Slack data', 'error')
        return redirect(url_for("auth.login"))
    resp_data = resp.json()
    if not 'user' in resp_data:
        flash('Invalid Slack data format', 'error')
        print(resp_data)
        return redirect(url_for("auth.login"))

    resp_user = resp_data['user']
    user = User.query.filter_by(sso_id=resp_user['id']).first()
    if not user:
        if current_user and current_user.is_authenticated:
            user = current_user
            user.sso_id = resp_user['id']
        else:
            user = User.query.filter_by(email=resp_user['email']).first()
            if user:
                # Update SSO identifier
                user.sso_id = resp_user['id']
                db.session.add(user)
                db.session.commit()
            else:
                user = User.create(
                    username=resp_user['name'].lower().replace(" ", "_"),
                    sso_id=resp_user['id'],
                    email=resp_user['email'],
                    password=random_password(),
                    active=True)
            user.socialize()
            login_user(user, remember=True)
            flash("Please complete your user account", 'info')
            return redirect(url_for("auth.user_profile"))
    login_user(user, remember=True)
    flash(u'Logged in via Slack')
    return redirect(url_for("public.home"))
