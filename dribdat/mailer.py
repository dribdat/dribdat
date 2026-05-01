# -*- coding: utf-8 -*-
"""Helper for sending mail."""

from flask import url_for, current_app
from flask_mailman import EmailMessage
from dribdat.utils import random_password  # noqa: I005


EMAIL_SIGNATURE = """ 
---
Your e-mail was registered on our event platform (Dribdat).
You can delete your account any time by editing your profile.
\n//d}}BD{t/
"""


def send_mail(msg, log_message=None):
    """Send an e-mail message."""
    if "mailman" not in current_app.extensions:
        current_app.logger.warning("E-mail extension has not been configured")
        return False
    if log_message:
        current_app.logger.info(log_message)
    msg.send(fail_silently=True)
    return True


def user_activation_message(user, act_hash):
    """Prepare a message to send to the user."""
    # base_url = url_for("public.home", _external=True)
    act_url = url_for(
        "auth.activate", userid=user.id, userhash=act_hash, _external=True
    )
    fqdn = current_app.config["SERVER_NAME"]
    from_email = current_app.config["MAIL_DEFAULT_SENDER"]
    # Populate message object
    msg = EmailMessage(from_email=from_email)
    msg.subject = "Your dribdat account"
    msg.body = (
        "👋🏾 Hello %s\n\n" % user.name
        + "🗝️ You are 1 click away from signing in:"
        + "\n\n%s\n\n" % act_url
        + "🚥 Is the link not working? Try to copy and paste this code:"
        + "\n\n  %s  \n\n" % act_hash
        + "💡 If you did not expect this e-mail, please change your password!\n"
        + "🏀 Thank you for using the Dribdat service at %s\n\n" % fqdn
        + EMAIL_SIGNATURE
    )
    # --------------------
    current_app.logger.debug(act_url)
    return msg


def user_activation(user):
    """Send an activation by e-mail."""
    act_hash = random_password(32)
    user.set_hashword(act_hash)
    user.save()
    msg = user_activation_message(user, act_hash)
    msg.to = [user.email]
    send_mail(msg, "Sending activation mail to user %d" % user.id)
    return act_hash


def user_registration(user_email):
    """Send an invitation by e-mail."""
    msg = user_invitation_message()
    msg.to = [user_email]
    send_mail(msg, "Sending registration mail")


def user_assignment_message(user, project, comment=""):
    """Sends an invitation email to a user."""
    from_email = current_app.config["MAIL_DEFAULT_SENDER"]
    msg = EmailMessage(from_email=from_email)
    msg.subject = "Dribdat: Project matching invitation"
    msg.to = [user.email]
    project_url = url_for("project.project_view", project_id=project.id, _external=True)
    body = "Hi %s,\n" % user.name
    if comment:
        body += "\n%s\n" % comment
    body += """
Based on a statistical algorithm that uses your preferences and profile
to help organize a diverse and inclusive event (HackIntegration), you
were matched with a potential project team:
    """
    body += "\n'%s'\n\n" % project.name
    body += "Check it out here: %s\n\n" % project_url
    body += "Tap the JOIN button if you agree!\n"
    body += EMAIL_SIGNATURE
    msg.body = body
    send_mail(msg, "Sending assignment mail to user %d" % user.id)


def user_invitation_message(project=None):
    """Craft an invitation message."""
    from_email = current_app.config["MAIL_DEFAULT_SENDER"]
    msg = EmailMessage(from_email=from_email)
    if project:
        act_url = url_for("project.project_star", project_id=project.id, _external=True)
        msg.subject = "Invitation: %s" % project.event.name
        msg.body = (
            "You are personally invited - please join us at %s!\n\n"
            % project.event.name
            + "🏀 We are interested in your contributions to '%s'.\n" % project.name
            + "🤼 Tap here to join the team: %s\n\n" % act_url
            + EMAIL_SIGNATURE
        )
    else:
        act_url = url_for("auth.register", _external=True)
        msg.subject = "Invitation to Dribdat"
        msg.body = (
            "You are invited to make a contribution to our sprint!\n\n"
            + "🏀 Tap here to create an account: %s\n\n" % act_url
            + EMAIL_SIGNATURE
        )
    return msg


def user_invitation(user_email, project):
    """Send an invitation by e-mail."""
    msg = user_invitation_message(project)
    msg.to = [user_email]
    return send_mail(msg, "Sending activation mail to %s" % user_email)


def notify_admin_message(about=""):
    fqdn = current_app.config["SERVER_NAME"]
    mlto = current_app.config["MAIL_NOTIFY_ADMIN"]
    mlfr = current_app.config["MAIL_DEFAULT_SENDER"]
    # Create a message object with these settings
    msg = EmailMessage(from_email=mlfr)
    msg.to = [mlto]
    msg.subject = "Notification from Dribdat"
    msg.body = "A quick message from %s:\n\n%s" % (fqdn, about)
    return msg


def notify_admin(about=""):
    """Send an admin some important message."""
    if current_app.config["MAIL_NOTIFY_ADMIN"] is None:
        # No e-mail address configured
        return False
    if "@" not in current_app.config["MAIL_NOTIFY_ADMIN"]:
        current_app.logger.warn("MAIL_NOTIFY_ADMIN must contain an e-mail address")
        return False
    msg = notify_admin_message(about)
    return send_mail(msg, "Sending admin a notification mail")
