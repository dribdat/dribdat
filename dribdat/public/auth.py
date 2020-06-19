# -*- coding: utf-8 -*-
"""Authentication views."""

from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session, current_app, jsonify)

from flask_login import login_user, logout_user, login_required, current_user

from dribdat.user.models import User, Event
from dribdat.extensions import login_manager
from dribdat.utils import flash_errors, random_password
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
    dsi = current_app.config["DRIBDAT_SLACK_ID"]
    return dsi is not None and dsi != ""


@blueprint.route("/hi", methods=["GET", "POST"])
def hi():
    if not slack.authorized:
        return redirect(url_for("slack.login"))
    resp = slack.get("/user")
    assert resp.ok
    return "You are @{login} on Slack".format(login=resp.json()["login"])

# current_app.config["DRIBDAT_SLACK_ID"]
# current_app.config["DRIBDAT_SLACK_SECRET"]
#     return slack_oauth.authorize(
#         callback=url_for("auth.slack_oauth_callback", _external=True)
#     )
#
# blueprint = make_slack_blueprint(
#     client_id="my-key-here",
#     client_secret="my-secret-here",
# )
# app.register_blueprint(blueprint, url_prefix="/login")
#
# @blueprint.route("/slack_callback")
# @slack_oauth.authorized_handler
# def slack_oauth_callback(resp):
#     if resp is None or not resp["ok"]:
#         flash('Access denied to Slack', 'error')
#         return redirect(url_for("public.home"))
#     user = User.query.filter_by(sso_id=resp['user']['id']).first()
#     if not user:
#         if current_user and current_user.is_authenticated:
#             user = current_user
#             user.sso_id = resp['user']['id']
#         else:
#             user = User.create(
#                 username=resp['user']['name'].lower().replace(" ", "_"),
#                 sso_id=resp['user']['id'],
#                 email=resp['user']['email'],
#                 password=random_password(),
#                 active=True)
#             user.socialize()
#             login_user(user, remember=True)
#             flash("Please complete your user account", 'info')
#             return redirect(url_for("auth.user_profile"))
#     login_user(user, remember=True)
#     flash(u'Logged in via Slack')
#     return redirect(url_for("public.home"))

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
                        username=form.username.data,
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


@blueprint.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    user = current_user
    form = UserForm(obj=user, next=request.args.get('next'))
    if form.validate_on_submit():
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
    return render_template('public/user.html', user=user, form=form)
