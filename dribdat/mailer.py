# -*- coding: utf-8 -*-
"""Helper for sending mail."""
from flask import url_for, current_app
from flask_mailman import EmailMessage
from dribdat.utils import random_password  # noqa: I005
import logging


def user_activation_message(user, act_hash):
    base_url = url_for('public.home', _external=True)
    act_url = url_for(
        'auth.activate',
        userid=user.id,
        userhash=act_hash,
        _external=True)
    from_email = current_app.config['MAIL_DEFAULT_SENDER']
    msg = EmailMessage(from_email=from_email)
    msg.subject = 'Your dribdat account'
    fqdn = base_url.replace('https://', '').replace('/', '')
    msg.body = \
        "Hello %s\n" % user.name \
        + "🗝️ You are one click away from signing into Dribdat\n\n" \
        + "Log in here: %s\n\n" % act_url \
        + "🏀 Thank you for signing up at %s\n" % fqdn \
        + "💡 If you did not expect this e-mail, please change your password!\n\n" \
        + "-- D}}BD{T --"

    logging.debug(act_url)
    return msg


def user_activation(user):
    """Send an activation by e-mail."""
    act_hash = random_password(32)
    user.set_hashword(act_hash)
    user.save()
    msg = user_activation_message(user, act_hash)
    if not 'mailman' in current_app.extensions:
        logging.warning('E-mail extension has not been configured')
        return act_hash
    msg.to = [user.email]
    logging.info('Sending activation mail to user %d' % user.id)
    msg.send(fail_silently=True)
    return act_hash


def user_invitation_message(project):
    base_url = url_for('public.home', _external=True)
    login_url = url_for(
        'auth.login',
        _external=True)
    act_url = url_for(
        'project.project_star',
        project_id=project.id,
        _external=True)
    from_email = current_app.config['MAIL_DEFAULT_SENDER']
    msg = EmailMessage(from_email=from_email)
    msg.subject = 'Invitation from event: %s' % project.event.name
    msg.body = \
        "You are personally invited - please join us!\n\n" \
        + "🏀 We are interested in your contributions to '%s'.\n\n" % project.name \
        + "🤼 Tap here to join the team: %s\n\n" % act_url \
        + "-- D}}BD{T --"
    return msg


def user_invitation(user_email, project):
    """Send an invitation by e-mail."""
    if not 'mailman' in current_app.extensions:
        logging.warning('E-mail extension has not been configured')
        return False
    msg = user_invitation_message(project)
    msg.to = [user_email]
    logging.info('Sending activation mail to %s' % user_email)
    msg.send(fail_silently=True)
    return True
