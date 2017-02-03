# Dribdat

*The stakes are high, the competition is ready. You will be measured, your progress tracked, your creativity analysed & compared. Think you have what it takes? Ready, steady, go!*

**Dribdat (from "Driven By Data") is an open platform for data-driven team collaboration, such as Hackathons.** It works as a website and project board for running exciting, productive events..with Impact Factor. We [created this tool](https://datalets.ch/dribdat/iot-2015/project/23/) after using plain wikis and forums for years, and after trying out a few proprietary tools that we felt limited us in one way or another.

The platform allows organisers and participants to aggregate project details from multiple sources (Markdown, Wikis, GitHub, Bitbucket), display challenges and projects in attractive dashboards, reuse the data through an API, plug in community tools ([Discourse](https://www.discourse.org/), [Slack](http://slack.com), [Let's Chat](http://sdelements.github.io/lets-chat/), etc.) and even [chatbots](https://github.com/schoolofdata-ch/sodabot) to enhance the hackathon.

## Deployment Quickstart

This project is ready for fast deployment to [Heroku](http://heroku.com):

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

You can configure your instance with the following basic environment variables:

* `SERVER_URL` - fully qualified domain name where the site is hosted
* `DRIBDAT_ENV` - 'dev' to enable debugging, 'prod' to optimise assets etc.
* `DRIBDAT_SECRET` - a long scary string for hashing your passwords - in Heroku this is set automatically
* `DATABASE_URL` - if you are using the Postgres add-on, this would be postgres://username:password@... - in Heroku this is set automatically
* `CACHE_TYPE` - in production, you can use built-in, Redis, Memcache to speed up your site (see `settings.py`)

If you would like to use external clients, like the chatbot, to remote control Dribdat you need to set:

* `DRIBDAT_APIKEY` - for connecting clients to the remote [API](#api)

OAuth 2.0 support is built in, currently fully supporting Slack, using these variables:

* `DRIBDAT_SLACK_ID` - an OAuth Client ID to enable [Sign in with Slack](https://api.slack.com/docs/sign-in-with-slack)
* `DRIBDAT_SLACK_SECRET` - ..and client secret. Set the redirect URL in your app's OAuth Settings to `<SERVER_URL>/slack_callback`

## Developer guide

[![Build Status](https://travis-ci.org/loleg/dribdat.svg?branch=master)](https://travis-ci.org/loleg/dribdat)

Run the following commands to bootstrap your environment.

```
git clone https://github.com/loleg/dribdat
cd dribdat
pip install -r requirements/dev.txt
```

By default in a dev environment, a SQLite database will be created in the root folder (`dev.db`). You can also install and configure your choice of DBMS [supported by SQLAlchemy](http://docs.sqlalchemy.org/en/rel_1_1/dialects/index.html).

Run the following to create your app's database tables and perform the initial migration:

```
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```

Finally, run this command to start the server:

```
python manage.py server
```

You will see a pretty welcome screen at http://localhost:5000

The first user that registers becomes an admin, so don't delay!

### Shell access

To open the interactive shell, run: `python manage.py shell` (or, using the [Heroku toolchain](https://devcenter.heroku.com/categories/command-line), `heroku run python manage.py shell`)

By default, you will have access to `app`, `db`, and the `User` model. For example, to promote to admin and reset the password of the first user:

```
u = User.query.first()
u.is_admin = True
u.set_password('Ins@nEl*/c0mpl3x')
u.save()
```

### Running Tests

To run all tests, run: `python manage.py test`

## Migrations

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

## API

There are a few API calls that admins can use to easily get to the data in Dribdat in CSV or JSON format.

Note that a print view of all projects is accessible from the Events admin console.

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

Push data into projects (WIP):

- `/api/project/push.json`

For details see `api.py`

## Credits

Developed by [Oleg Lavrovsky](http://datalets.ch) based on [Steven Loria's flask-cookiecutter](https://github.com/sloria/cookiecutter-flask).

With thanks to [Swisscom](http://swisscom.com)'s F. Wieser and M.-C. Gasser for conceptual inputs and financial support of the first release of this project.
