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
from flask_dance.contrib.azure import azure
from flask_dance.contrib.github import github

blueprint = Blueprint('auth', __name__, static_folder="../static")

def current_event():
    return Event.query.filter_by(is_current=True).first()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

def oauth_type():
    """Check if Slack or another OAuth has been configured"""
    if "OAUTH_TYPE" in current_app.config:
        return current_app.config["OAUTH_TYPE"].lower()
    else:
        return None


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    # Skip login form on forced SSO
    if request.method == "GET" and current_app.config["OAUTH_SKIP_LOGIN"]:
        if not request.args.get('local') and oauth_type():
            return redirect(url_for(oauth_type() + '.login'))
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
    return render_template("public/login.html", current_event=current_event(), form=form, oauth_type=oauth_type())


@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    """Register new user."""
    if current_app.config['DRIBDAT_NOT_REGISTER']:
        flash("Registration currently not possible.", 'warning')
        return redirect(url_for("auth.login", local=1))
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
        elif current_app.config['DRIBDAT_USER_APPROVE']:
            new_user.active = False
            new_user.save()
            flash("Thank you for registering. New accounts require approval from the event organizers. Please update your profile and await activation.", 'warning')
        else:
            flash("Thank you for registering. You can now log in and submit projects.", 'success')
        login_user(new_user, remember=True)
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    return render_template('public/register.html', current_event=current_event(), form=form, oauth_type=oauth_type())


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
    return render_template('public/forgot.html', current_event=current_event(), oauth_type=oauth_type())


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

def get_or_create_sso_user(sso_id, sso_name, sso_email, sso_webpage=''):
    """ Matches a user account based on SSO_ID """
    sso_id = str(sso_id)
    user = User.query.filter_by(sso_id=sso_id).first()
    if not user:
        if current_user and current_user.is_allowed:
            user = current_user
            user.sso_id = sso_id
        else:
            user = User.query.filter_by(email=sso_email).first()
            if user:
                # Update SSO identifier
                user.sso_id = sso_id
                db.session.add(user)
                db.session.commit()
            else:
                username = sso_name.lower().replace(" ", "_")
                user = User.query.filter_by(username=username).first()
                if user:
                    flash('Duplicate username (%s), please try again or contact an admin.' % username, 'warning')
                    return redirect(url_for("auth.login", local=1))
                user = User.create(
                    username=username,
                    sso_id=sso_id,
                    email=sso_email,
                    webpage_url=sso_webpage,
                    password=random_password(),
                    active=True)
            user.socialize()
            login_user(user, remember=True)
            flash("Welcome! Please complete your user account.", 'info')
            return redirect(url_for("auth.user_profile"))
    login_user(user, remember=True)
    flash(u'Logged in - welcome!', 'success')
    if current_event():
        return redirect(url_for("public.event", event_id=current_event().id))
    else:
        return redirect(url_for("public.home"))


@blueprint.route("/slack_login", methods=["GET", "POST"])
def slack_login():
    if not slack.authorized:
        flash('Access denied to Slack', 'danger')
        return redirect(url_for("auth.login", local=1))

    resp = slack.get("https://slack.com/api/users.identity")
    if not resp.ok:
        flash('Unable to access Slack data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_data = resp.json()
    if not 'user' in resp_data:
        flash('Invalid Slack data format', 'danger')
        print(resp_data)
        return redirect(url_for("auth.login", local=1))
    resp_user = resp_data['user']
    return get_or_create_sso_user(
        resp_user['id'],
        resp_user['name'],
        resp_user['email'],
    )


@blueprint.route("/azure_login", methods=["GET", "POST"])
def azure_login():
    if not azure.authorized:
        flash('Access denied to Azure', 'danger')
        return redirect(url_for("auth.login", local=1))

    resp = azure.get("https://graph.microsoft.com/v1.0/me/")
    if not resp.ok:
        flash('Unable to access Azure data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_user = resp.json()
    if not 'mail' in resp_user:
        flash('Invalid Azure data format', 'danger')
        print(resp_user)
        return redirect(url_for("auth.login", local=1))
    return get_or_create_sso_user(
        resp_user['id'],
        resp_user['displayName'],
        resp_user['mail'],
    )

@blueprint.route("/github_login", methods=["GET", "POST"])
def github_login():
    if not github.authorized:
        flash('Access denied - please try again', 'warning')
        return redirect(url_for("auth.login", local=1))

    resp = github.get("/user")
    if not resp.ok:
        flash('Unable to access GitHub data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_user = resp.json()
    if not 'email' in resp_user or not 'login' in resp_user:
        flash('Invalid GitHub data format', 'danger')
        print(resp_user)
        return redirect(url_for("auth.login", local=1))

    resp_emails = github.get("/user/emails")
    if not resp.ok:
        flash('Unable to access GitHub e-mail data', 'danger')
        return redirect(url_for("auth.login", local=1))
    for u in resp_emails.json():
        if u['primary'] and u['verified']:
            return get_or_create_sso_user(
                resp_user['id'],
                resp_user['login'],
                u['email'],
                'https://github.com/%s' % resp_user['login']
            )
    flash('Please verify an e-mail with GitHub', 'danger')
    return redirect(url_for("auth.login", local=1))
