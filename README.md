# Dribdat

[![Travis](https://travis-ci.org/datalets/dribdat.svg?branch=master)](https://travis-ci.org/datalets/dribdat)
[![Coveralls](https://coveralls.io/repos/github/datalets/dribdat/badge.svg?branch=master)](https://coveralls.io/github/datalets/dribdat?branch=master)
[![Mattermost](https://img.shields.io/badge/Mattermost-chat-blue.svg)](https://team.opendata.ch/signup_user_complete/?id=74yuxwruaby9fpoukx9bmoxday)

### An open source platform for time-limited team-based data-driven solutions-focused collaboration known as the *Hackathon*.

If you need help or advice in setting up your event, or would like to contribute to the project: please get in touch via [datalets.ch](https://datalets.ch) or [GitHub Issues](https://github.com/hackathons-ftw/dribdat/issues).

For more background and references, see [USAGE](USAGE.md) and [ABOUT](ABOUT.md). The rest of this document has details for deploying the application.

# Quickstart

This project can be deployed to any server capable of serving Python applications, and is set up for fast deployment to the [Heroku](http://heroku.com) cloud:

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

Add the **nodejs** build pack in the _Settings_ tab of Heroku to get everything working properly.

The first user that registers becomes an admin, so don't delay!

## Configuration

You can configure your instance with the following **basic environment** variables:

* `TIME_ZONE` - set if your event is not in UTC time (e.g. "Europe/Zurich" - see [pytz docs](https://pythonhosted.org/pytz/))
* `SERVER_URL` - fully qualified domain name where the site is hosted
* `SERVER_SSL` - redirect all visitors to HTTPS, applying CSP
* `CSP_DIRECTIVES` - configure content security policy - see [Talisman docs](https://github.com/GoogleCloudPlatform/flask-talisman#content-security-policy)
* `DATABASE_URL` - if you are using the Postgres add-on, this would be postgres://username:password@... - in Heroku this is set automatically
* `CACHE_TYPE` - speed up the site with built-in, Redis, Memcache - see [Flask-Caching](https://pythonhosted.org/Flask-Caching/)

The following options can be used to toggle **application features**:

* `DRIBDAT_ENV` - 'dev' to enable debugging, 'prod' to optimise assets etc.
* `DRIBDAT_SECRET` - a long scary string for hashing your passwords - in Heroku this is set automatically
* `DRIBDAT_APIKEY` - for connecting clients to the remote [API](#api)
* `DRIBDAT_NOT_REGISTER` - set to True to disallow creating accounts on this server
* `DRIBDAT_SHOW_SUBMITS` - set to False to moderate resource submissions on the site
* `DRIBDAT_THEME` - can be set to one of the [Bootswatch themes](https://bootswatch.com/)
* `DRIBDAT_CLOCK` - use 'up' or 'down' to change the position, or 'off' to hide the countdown

Support for **Web analytics** can be configured using one of the following variables:

* `ANALYTICS_FATHOM` ([Fathom](https://usefathom.com/) - with optional `ANALYTICS_FATHOM_SITE` if you use a custom site)
* `ANALYTICS_SIMPLE` ([Simple Analytics](https://simpleanalytics.com))
* `ANALYTICS_GOOGLE` (starts with "UA-...")
* `ANALYTICS_HREF` - an optional link in the footer to a public dashboard for your analytics

OAuth 2.0 support for **Single Sign-On** is currently available using [Flask Dance](https://flask-dance.readthedocs.io/) (see [issue #118](https://github.com/hackathons-ftw/dribdat/issues/118)). To authenticate your users, the following variables should be set:

* `OAUTH_TYPE` - e.g. 'Slack'
* `OAUTH_ID` - the Client ID of your app (e.g. from [api.slack.com](https://api.slack.com/apps/))
* `OAUTH_SECRET` - the Client Secret of your app
* `OAUTH_DOMAIN` - (optional) subdomain of your Slack instance, or AD tenant for Azure

For **uploading images** and other files directly within dribdat, you can configure S3 through Amazon and compatible providers:

* `S3_KEY` - the access key (20 characters, all caps)
* `S3_SECRET` - the generated secret (long, mixed case)
* `S3_BUCKET` - the name of your S3 bucket
* `S3_REGION` - defaults to 'eu-west-1'
* `S3_FOLDER` - leave blank unless you want to store to a subfolder
* `S3_HTTPS` - the URL for web access to your bucket's public files
* `MAX_CONTENT_LENGTH` - defaults to 1048576 bytes (1 MB) file size

**Tip**: Use `.flaskenv` or `.env` to store environment variables for local development.

## API

There are a number of API calls that admins can use to easily get to the data in Dribdat in CSV or JSON format. These are linked in the About page in a running app. Additionally, the site has a  See GitHub issues for development status.

Basic data on an event:

- `/api/event/<EVENT ID>/info.json`
- `/api/event/current/info.json`

Retrieve data on all projects from an event:

- `/api/event/<EVENT ID>/projects.csv`
- `/api/event/<EVENT ID>/projects.json`
- `/api/event/current/projects.json`

Recent activity in projects (all or specific):

- `/api/project/activity.json`
- `/api/<PROJECT ID>/activity.json`

Search project contents:

- `/api/project/search.json?q=<text_query>`

Use the `limit` query parameter to get more or less than 10 results.

If you would like to use external clients, like the chatbot, to remote control Dribdat you need to set `DRIBDAT_APIKEY`. The (experimental) call used to push data into projects is:

- `/api/project/push.json`

For more details see [api.py](dribdat/public/api.py)

# Developer guide

Install Python, Virtualenv and Pip, or [Poetry](https://python-poetry.org/) to start working with the code.

You may need to install additional libraries (`libffi`) for the [misaka](http://misaka.61924.nl/) package, which depends on [CFFI](https://cffi.readthedocs.io/en/latest/installation.html#platform-specific-instructions), e.g. `sudo dnf install libffi-devel`

Run the following commands from the repository root folder to bootstrap your environment:

```
poetry shell
poetry install
```

Or using plain pip:

```
pip install -r requirements/dev.txt
```

By default in a dev environment, a SQLite database will be created in the root folder (`dev.db`). You can also install and configure your choice of DBMS [supported by SQLAlchemy](http://docs.sqlalchemy.org/en/rel_1_1/dialects/index.html).

Run the following to create your app's database tables and perform the initial migration:

```
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```

Install frontend resources using [Yarn](https://yarnpkg.com/en/docs/getting-started):

```
yarn install
```

Finally, run this command (or just `debug.sh`) to start the server:

```
FLASK_DEBUG=1 python manage.py run
```

You will see a pretty welcome screen at http://127.0.0.1:5000

## Coding tips

This section has some advice for developers and operators.

### Shell access

To open the interactive shell, run: `python manage.py shell` (or, using the [Heroku toolchain](https://devcenter.heroku.com/categories/command-line), `heroku run python manage.py shell`). By default, you will have access to the `User` model, as well as Event, Project, Category, Activity.

### Running Tests

To run all tests, whose source is in the **tests** folder, run: `python manage.py test`

### Migrations

Whenever a database migration needs to be made. Run the following commands:

```
python manage.py db migrate
```

This will generate a new migration script. Then run:

```
python manage.py db upgrade
```

To apply the migration. Watch out for any errors in the process.

For a full migration command reference, run `python manage.py db --help`.

## Troubleshooting

A quick guide to a few common errors:

### Front-end is broken

If you are not seeing the icons and other things are not working on the front end, chances are you need to run a build. Just type `yarn` in the home folder, or run the **Build** command in your _Resources_ tab in Heroku.

### Embedding the front-end

There is an Embed button in the event page and in the admin which provides you with code for an IFRAME that just contains the hexagrid. If you would like to embed the entire application, and find it more intuitive to hide the navigation, add `?clean=1` to the URL. To also hide the top header, use `?minimal=1`.

### Cannot upgrade database

If you get errors like *ERROR [alembic.env] Can't locate revision identified by 'aa969b4f9f51'*, usually the fix is to drop the migration history table (`psql -c "drop table alembic_version"`), and again `db init .. db migrate .. db upgrade`. You can do this in your database client.

In the case of Heroku, there's a separate process called **Upgrade** which you can find in your _Resources_ tab. Run it and watch the logs for a minute until it completes, then turn it off again.

### Restore admin access

Create a user account if you do not already have one. From the console, run `./manage.py shell` then to promote to admin and/or reset the password of a user called "admin":

```
u = User.query.filter(User.username=='admin').first()
u.is_admin = True
u.set_password('Ins@nEl*/c0mpl3x')
u.save()
```

### Test locally using SSL

Some development scenarios and OAuth testing requires SSL. To use this in development with self-signed certificates (you will get a browser warning), start the server with `./manage.py run --cert=adhoc`

# Credits

See [Contributors](https://github.com/dataletsch/dribdat/graphs/contributors) for a list of people who have made changes to the code, and [Forks](https://github.com/dataletsch/dribdat/network/members) to find some other users of this project.

This project is currently mantained by [@loleg](https://github.com/loleg) and [@gonzalocasas](https://github.com/gonzalocasas).

Special thanks to the [Open Data](https://opendata.ch), [Open Networking](https://opennetworkinfrastructure.org/) and [Open Source](https://dinacon.ch) communities in Switzerland for the many trials and feedbacks. We are also grateful to F. Wieser and M.-C. Gasser at [Swisscom](http://swisscom.com) for conceptual inputs and financial support at an early stage of this project. This code is originally based on Steven Loria's [flask-cookiecutter](https://github.com/sloria/cookiecutter-flask), which we encourage you to use in YOUR next hackathon!

Additional and :heart:-felt thanks for testing and feedback to:

- [Alexandre Cotting](https://github.com/Cotting)
- [Anthony Ritz](https://github.com/RitzAnthony)
- [Chris Mutel](https://github.com/cmutel)
- [Fabien Schwob](https://github.com/jibaku)
- [Jonathan Sobel](https://github.com/JonathanSOBEL)
- [@jonhesso](https://github.com/jonHESSO)
- [@khashashin](https://github.com/khashashin)
- [@philshem](https://github.com/philshem)
- [Thomas Amberg](https://github.com/tamberg)
