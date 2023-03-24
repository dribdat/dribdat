# -*- coding: utf-8 -*-
"""Helper for sending mail."""
from flask import url_for
from flask_mailman import EmailMessage
from dribdat.utils import random_password  # noqa: I005


async def user_activation(app, user):
    """Send an activation by e-mail."""
    act_hash = random_password(32)
    with app.app_context():
        user.set_hashword(act_hash)
        user.save()
        base_url = url_for('public.home', _external=True)
        act_url = url_for(
            'auth.activate',
            userid=user.id,
            userhash=act_hash,
            _external=True)
        msg = EmailMessage()
        msg.subject = 'Your dribdat account'
        msg.body = \
            "Thanks for signing up at %s\n\n" % base_url \
            + "Tap here to activate your account:\n\n%s" % act_url
        msg.to = [user.email]
        app.logger.info('Sending mail to user %d' % user.id)
        await msg.send()
        return True

