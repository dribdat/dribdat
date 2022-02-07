This document contains additional tips for working with dribdat.

# Troubleshooting

Guidance to common errors is listed below.
For more background references, see the [README](README.md).

## Add results to my own web page

There is an Embed button in the event page and in the admin which provides you with code for an IFRAME that just contains the hexagrid. If you would like to embed the entire application, and find it more intuitive to hide the navigation, add `?clean=1` to the URL. To also hide the top header, use `?minimal=1`. You might also invoke the [dribdat API](#API) to pull data from the platform.

## Navigation is not visible

Dark Bootswatch themes do not play well with the *navbar-light* component used in our layout (`nav.html`). Override the styles by hand using the `DRIBDAT_CSS_URL` environment variable.

## Need help setting up SSO

To get client keys, go to the [Slack API](https://api.slack.com/apps/), [Azure portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade), or add the [GitHub App](https://github.com/apps/dribdat) to your account or organization. You can also use [custom OAuth 2](https://flask-dance.readthedocs.io/en/latest/providers.html#custom) provider if you provide all external registration URLs.

Cannot determine SSO callback for app registration? Try `<my server url>/oauth/slack/authorized` (replace `slack` with your OAuth provider).

## Restore admin access

Create a user account if you do not already have one. From the console, run `./manage.py shell` then to promote to admin and/or reset the password of a user called "admin":

```
u = User.query.filter(User.username=='admin').first()
u.is_admin = True
u.set_password('Ins@nEl*/c0mpl3x')
u.save()
```

## Cannot upgrade database

In local deployment, you will need to upgrade the database using `./manage.py db upgrade`. On Heroku, a deployment process called **Release** runs automatically.

If you get errors like *ERROR [alembic.env] Can't locate revision identified by 'aa969b4f9f51'*, your migration history is out of sync. You can set `FORCE_MIGRATE` to 1 when you run releases, however changes to the column sizes and other schema details will not be deployed. Instead, it is better to verify the latest schema specifications in the `migrations` folder, fix anything that is out of sync, and then update the alembic version, e.g.:

```
alter table projects alter column webpage_url type character varying(2048);
insert into alembic_version values ('7c3929047190')
```

If you get errors like *Invalid input value for enum activity_type*, there were issues in upgrading your instance that may require a manual SQL entry. Try running these commands in your `psql` console:

```
ALTER TYPE activity_type ADD VALUE 'boost';
ALTER TYPE activity_type ADD VALUE 'review';
```

See also further instructions in the `force-migrate.sh` script.

## Test locally using SSL

Some development scenarios and OAuth testing requires SSL. To use this in development with self-signed certificates (you will get a browser warning), start the server with `./manage.py run --cert=adhoc`

You can also try to test SSO providers with `OAUTHLIB_INSECURE_TRANSPORT=true` (do not use in production!)

## Installation on Alpine Linux

The project has so far mostly been developed on Fedora and Ubuntu Linux. Users on Alpine, BSD and other distributions are welcome to share their experience with us in the Issues. Some additional system packages are needed for a successful local (non-Docker) deployment:

```
apk add libxml2-dev libxslt-dev rust cargo
```
