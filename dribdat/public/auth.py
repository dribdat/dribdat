# -*- coding: utf-8 -*-
"""Authentication views."""

from flask import (Blueprint, request, render_template, flash, url_for,
                   redirect, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.slack import slack
from flask_dance.contrib.azure import azure  # noqa: I005
from flask_dance.contrib.github import github
from dribdat.sso.auth0 import auth0
from dribdat.sso.mattermost import mattermost
from dribdat.sso.hitobito import hitobito
# Dribdat modules
from dribdat.user.models import User, Event, Role
from dribdat.extensions import login_manager  # noqa: I005
from dribdat.utils import flash_errors, random_password, sanitize_input
from dribdat.user.forms import RegisterForm, EmailForm, LoginForm, UserForm
from dribdat.database import db
from dribdat.mailer import user_activation
from datetime import datetime
# noqa: I005

blueprint = Blueprint('auth', __name__, static_folder="../static")


def current_event():
    """Return the first featured event."""
    return Event.query.filter_by(is_current=True).first()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


def oauth_type():
    """Check if Slack or another OAuth has been configured."""
    if "OAUTH_TYPE" in current_app.config:
        return current_app.config["OAUTH_TYPE"].lower()
    else:
        return None


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    """Handle the login route."""
    # Skip login form on forced SSO
    if request.method == "GET" and current_app.config["OAUTH_SKIP_LOGIN"]:
        if not request.args.get('local') and oauth_type():
            return redirect(url_for(oauth_type() + '.login'))
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user, remember=True)
            if not form.user.active:
                # Note: continue to profile page, where user is warned
                username = current_user.username
                return redirect(url_for('public.user', username=username))
            # Regular user greeting
            flash("Welcome! Time to make something awesome. ≧◡≦",
                  'success')
            return redirect(url_for("public.home"))
        else:
            flash_errors(form)
    logout_user()
    return render_template("public/login.html",
                           form=form, oauth_type=oauth_type())


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
    if not form.validate_on_submit():
        flash_errors(form)
        logout_user()
        return render_template('public/register.html',
                               form=form, oauth_type=oauth_type())
    # Continue with user creation
    sane_username = sanitize_input(form.username.data)
    new_user = User.create(
                    username=sane_username,
                    email=form.email.data,
                    webpage_url=form.webpage_url.data,
                    password=form.password.data,
                    active=True)
    new_user.socialize()
    if User.query.count() == 1:
        # This is the first user account - promote it
        new_user.is_admin = True
        new_user.save()
        flash("Administrative user created - oh joy!", 'success')
    elif current_app.config['DRIBDAT_USER_APPROVE']:
        # Approval of new user accounts required
        new_user.active = False
        new_user.save()
        if current_app.config['MAIL_SERVER']:
            user_activation(current_app, new_user)
            flash("New accounts require activation. "
                  + "Please click the dribdat link in your e-mail.", 'success')
        else:
            flash("New accounts require approval from the event organizers. "
                  + "Please update your profile and await activation.",
                  'success')
    else:
        flash(
            "Thank you for registering. You can now log in and submit "
            + "projects.", 'success')
    # New user created: start session and go home
    login_user(new_user, remember=True)
    return redirect(url_for('public.home'))


@blueprint.route("/activate/<userid>/<userhash>", methods=['GET'])
def activate(userid, userhash):
    """Activate or reset new user account."""
    a_user = User.query.filter_by(id=userid).first_or_404()
    if a_user.check_hashword(userhash):
        a_user.hashword = None
        a_user.active = True
        a_user.save()
        login_user(a_user, remember=True)
        flash("Welcome! Your user account has been activated.", 'success')
        return redirect(url_for('auth.user_profile'))
    flash("Activation not found. Try again, or ask an organizer.", 'warning')
    logout_user()
    return redirect(url_for('public.home'))


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
    form = EmailForm(request.form)
    if not form.validate_on_submit():
        flash_errors(form)
    return render_template(
            'public/forgot.html',
            form=form,
            oauth_type=oauth_type())


@blueprint.route("/passwordless/", methods=['POST'])
def passwordless():
    """Log in a new user via e-mail."""
    if current_app.config['DRIBDAT_NOT_REGISTER'] or \
       not current_app.config['MAIL_SERVER']:
        flash("Passwordless login currently not possible.", 'warning')
        return redirect(url_for("auth.login", local=1))
    form = EmailForm(request.form)
    if not form.validate_on_submit():
        flash_errors(form)
        return redirect(url_for('auth.forgot'))
    # Continue with user activation
    flash(
        "If your account exists, you will shortly receive "
        + "an activation mail. Check your Spam folder if you do not. "
        + "Then click the link in that e-mail to log into this application.",
        'success')
    a_user = User.query.filter_by(email=form.email.data).first()
    if a_user:
        # Continue with reset
        user_activation(current_app, a_user)
    else:
        current_app.logger.warn('User not found: %s' % form.email.data)
    # Don't let people spy on your address
    return redirect(url_for("auth.login"))


@blueprint.route('/user/profile/delete', methods=['POST'])
@login_required
def delete_my_account():
    """Delete the current user profile."""
    current_user.delete()
    logout_user()
    flash('We are sorry to see you go. Your profile has been deleted.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """Display or edit the current user profile."""
    user = current_user
    user_is_valid = True
    if not user.active:
        flash('This user account is under review. Please update your profile '
              + ' and contact the organizing team to access all functions of '
              + 'this platform.', 'warning')

    form = UserForm(obj=user, next=request.args.get('next'))
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by('name')]

    # Check conflicting PKs
    if form.email.data != user.email:
        if User.query.filter_by(email=form.email.data).first() is not None:
            flash('This e-mail address is already registered.', 'error')
            user_is_valid = False

    if user.sso_id:
        # Do not allow changing password on SSO
        del form.password

    # Validation has passed
    if form.validate_on_submit() and user_is_valid:
        # Assign roles
        user.roles = [Role.query.filter_by(
            id=r).first() for r in form.roles.data]
        del form.roles

        # Sanitize username
        user.username = sanitize_input(form.username.data)
        del form.username

        # Assign password if changed
        originalhash = user.password
        form.populate_obj(user)
        # Do not allow changing password on SSO
        if not user.sso_id:
            if form.password.data:
                user.set_password(form.password.data)
            else:
                user.password = originalhash
                user.updated_at = datetime.utcnow()

        db.session.add(user)
        db.session.commit()
        user.socialize()
        flash('Profile updated.', 'success')
        return redirect(url_for('public.user', username=user.username))

    if not form.roles.choices:
        del form.roles
    else:
        form.roles.data = [(r.id) for r in user.roles]
    return render_template('public/useredit.html',
                           oauth_type=oauth_type(),
                           user=user, form=form,
                           active='profile')


def get_or_create_sso_user(sso_id, sso_name, sso_email, sso_webpage=''):
    """Match a user account based on SSO_ID."""
    sso_id = str(sso_id)
    user = User.query.filter_by(sso_id=sso_id).first()
    if not user:
        if isinstance(current_user, User) and current_user.active:
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
                    flash(
                        "Duplicate username (%s) - " % username
                        + 'please change it, or contact an admin for help.',
                        'warning')
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
    if not user.active:
        flash('This user account is under review. Please update your profile '
              + 'and contact the organizing team to access all functions of '
              + 'this platform.', 'warning')
    else:
        flash(u'Logged in! Time to make something awesome ≧◡≦', 'success')

    if current_event():
        return redirect(url_for("public.event", event_id=current_event().id))
    else:
        return redirect(url_for("public.home"))


@blueprint.route("/slack_login", methods=["GET", "POST"])
def slack_login():
    """Handle login via Slack."""
    if not slack.authorized:
        flash('Access denied to Slack', 'danger')
        return redirect(url_for("auth.login", local=1))
    # Get remote user data
    resp = slack.get("https://slack.com/api/users.identity")
    if not resp.ok:
        flash('Unable to access Slack data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_data = resp.json()
    if 'user' not in resp_data:
        flash('Invalid Slack data format', 'danger')
        # print(resp_data)
        return redirect(url_for("auth.login", local=1))
    resp_user = resp_data['user']
    return get_or_create_sso_user(
        resp_user['id'],
        resp_user['name'],
        resp_user['email'],
    )


@blueprint.route("/azure_login", methods=["GET", "POST"])
def azure_login():
    """Handle login via Azure."""
    if not azure.authorized:
        flash('Access denied to Azure', 'danger')
        return redirect(url_for("auth.login", local=1))
    # Get remote user data
    resp = azure.get("https://graph.microsoft.com/v1.0/me/")
    if not resp.ok:
        flash('Unable to access Azure data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_user = resp.json()
    if 'mail' not in resp_user:
        flash('Invalid Azure data format', 'danger')
        # print(resp_user)
        return redirect(url_for("auth.login", local=1))
    return get_or_create_sso_user(
        resp_user['id'],
        resp_user['displayName'],
        resp_user['mail'],
    )


@blueprint.route("/github_login", methods=["GET", "POST"])
def github_login():
    """Handle login via GitHub."""
    if not github.authorized:
        flash('Access denied - please try again', 'warning')
        return redirect(url_for("auth.login", local=1))
    # Get remote user data
    resp = github.get("/user")
    if not resp.ok:
        flash('Unable to access GitHub data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_user = resp.json()
    if 'email' not in resp_user or 'login' not in resp_user:
        flash('Invalid GitHub data format', 'danger')
        # print(resp_user)
        return redirect(url_for("auth.login", local=1))
    # Get remote profile data
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


@blueprint.route("/auth0_login", methods=["GET", "POST"])
def auth0_login():
    """Handle login via Auth0."""
    if not auth0.authorized:
        flash('Access denied to Auth0', 'danger')
        return redirect(url_for("auth.login", local=1))
    # Get remote user data
    resp = auth0.get("/userinfo")
    if not resp.ok:
        flash('Unable to access Auth0 data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_data = resp.json()
    if 'nickname' not in resp_data:
        flash('Invalid Auth0 data format', 'danger')
        # print(resp_data)
        return redirect(url_for("auth.login", local=1))
    return get_or_create_sso_user(
        resp_data['sub'],
        resp_data['nickname'],
        resp_data['email'],
    )


@blueprint.route("/mattermost_login", methods=["GET", "POST"])
def mattermost_login():
    """Handle login via Mattermost."""
    if not mattermost.authorized:
        flash('Access denied to Mattermost', 'danger')
        return redirect(url_for("auth.login", local=1))
    # Get remote user data
    resp = mattermost.get("/api/v4/users/me")
    if not resp.ok:
        flash('Unable to access Mattermost data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_data = resp.json()
    # print(resp_data)
    username = None
    if 'nickname' in resp_data:
        username = resp_data['nickname']
    elif 'username' in resp_data:
        username = resp_data['username']
    if username is None:
        flash('Invalid Mattermost data format', 'danger')
        return redirect(url_for("auth.login", local=1))
    return get_or_create_sso_user(
        resp_data['id'],
        username,
        resp_data['email'],
    )


@blueprint.route("/hitobito_login", methods=["GET", "POST"])
def hitobito_login():
    """Handle login via hitobito."""
    if not hitobito.authorized:
        flash('Access denied to hitobito', 'danger')
        return redirect(url_for("auth.login", local=1))
    # Get remote user data
    resp = hitobito.get("/en/oauth/profile", headers={'X-Scope': 'name'})
    if not resp.ok:
        flash('Unable to access hitobito data', 'danger')
        return redirect(url_for("auth.login", local=1))
    resp_data = resp.json()
    #print(resp_data)
    username = None
    if 'nickname' in resp_data and resp_data['nickname'] is not None:
        username = resp_data['nickname']
    elif 'first_name' in resp_data and 'last_name' in resp_data:
        fn = resp_data['first_name'].lower().strip()
        ln = resp_data['last_name'].lower().strip()
        username = "%s_%s" % (fn, ln)
    if username is None:
        flash('Invalid hitobito data format', 'danger')
        return redirect(url_for("auth.login", local=1))
    return get_or_create_sso_user(
        resp_data['id'],
        username,
        resp_data['email'],
    )

