# -*- coding: utf-8 -*-
"""Helper for sending mail."""
from flask import url_for, current_app
from flask_mailman import EmailMessage
from dribdat.utils import random_password  # noqa: I005
import logging


def user_activation(user):
    """Send an activation by e-mail."""
    act_hash = random_password(32)
    user.set_hashword(act_hash)
    user.save()
    base_url = url_for('public.home', _external=True)
    act_url = url_for(
        'auth.activate',
        userid=user.id,
        userhash=act_hash,
        _external=True)
    if not 'mailman' in current_app.extensions:
        logging.warning('E-mail extension has not been configured')
        return act_hash
    msg = EmailMessage()
    msg.subject = 'Your dribdat account'
    msg.body = \
        "Hello %s,\n" % user.username \
        + "Thanks for signing up at %s\n\n" % base_url \
        + "Tap here to activate your account:\n\n%s" % act_url
    msg.to = [user.email]
    logging.info('Sending activation mail to user %d' % user.id)
    logging.debug(act_url)
    msg.send(fail_silently=True)
    return act_hash


def user_invitation(user_email, project):
    """Send an invitation by e-mail."""
    base_url = url_for('public.home', _external=True)
    act_url = url_for(
        'project.project_star',
        project_id=project.id,
        _external=True)
    login_url = url_for(
        'auth.login',
        _external=True)
    if not 'mailman' in current_app.extensions:
        logging.warning('E-mail extension has not been configured')
        return False
    msg = EmailMessage()
    msg.subject = 'Join the [%s] team on dribdat' % project.name
    msg.body = \
        "You are invited - please join us!\n" \
        + "1. Login to dribdat at: %s\n\n" % login_url \
        + "2. Tap here to join your team: %s\n\n" % act_url \
        + "3. Contribute to %s" % project.name
    msg.to = [user_email]
    logging.info('Sending activation mail to %s' % user_email)
    msg.send(fail_silently=True)
    return True
