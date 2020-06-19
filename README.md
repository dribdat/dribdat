# Dribdat

[![Travis](https://travis-ci.org/datalets/dribdat.svg?branch=master)](https://travis-ci.org/datalets/dribdat)
[![Coveralls](https://coveralls.io/repos/github/datalets/dribdat/badge.svg?branch=master)](https://coveralls.io/github/datalets/dribdat?branch=master)
[![Mattermost](https://img.shields.io/badge/Mattermost-chat-blue.svg)](https://team.opendata.ch/signup_user_complete/?id=74yuxwruaby9fpoukx9bmoxday)

An open source platform for data-driven team collaboration, such as *Hackathons*.

If you need help or advice in setting up your event, or would like to contribute to the project: please get in touch via [datalets.ch](https://datalets.ch) or [GitHub Issues](https://github.com/datalets/dribdat/issues).

For more background and references, see [USAGE](USAGE.md) and [ABOUT](ABOUT.md). The rest of this document has details for deploying the application.

## Quickstart

This project can be deployed to any server capable of serving Python applications, and is set up for fast deployment to the [Heroku](http://heroku.com) cloud:

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

You can configure your instance with the following basic environment variables:

* `SERVER_URL` - fully qualified domain name where the site is hosted
* `DRIBDAT_ENV` - 'dev' to enable debugging, 'prod' to optimise assets etc.
* `DRIBDAT_SECRET` - a long scary string for hashing your passwords - in Heroku this is set automatically
* `DATABASE_URL` - if you are using the Postgres add-on, this would be postgres://username:password@... - in Heroku this is set automatically
* `CACHE_TYPE` - in production, you can use built-in, Redis, Memcache to speed up your site (see `settings.py`)

If you would like to use external clients, like the chatbot, to remote control Dribdat you need to set:

* `DRIBDAT_APIKEY` - for connecting clients to the remote [API](#api)

OAuth 2.0 support is currently not available. For information see [issue #118](https://github.com/dataletsch/dribdat/issues/118)

## API

There are a number of API calls that admins can use to easily get to the data in Dribdat in CSV or JSON format. See GitHub issues for [development status](https://github.com/datalets/dribdat/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+API).

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

For more details see [api.py](dribdat/public/api.py)

## Developer guide

Install Python, Virtualenv and Pip or [Poetry](https://python-poetry.org/) to start working with the code.

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

Finally, run this command to start the server:

```
FLASK_DEBUG=1 python manage.py run
```

You will see a pretty welcome screen at http://localhost:5000

The first user that registers becomes an admin, so don't delay!

### Shell access

To open the interactive shell, run: `python manage.py shell` (or, using the [Heroku toolchain](https://devcenter.heroku.com/categories/command-line), `heroku run python manage.py shell`)

By default, you will have access to the `User` model, as well as Event, Project, Category, Activity. For example, to promote to admin and reset the password of the first user:

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

If you get errors like *ERROR [alembic.env] Can't locate revision identified by 'aa969b4f9f51'*, usually the fix is to drop the migration history table, and again `db init .. db migrate .. db upgrade`. You can do this in your database client, or with a line like this in the case of Heroku:

`heroku pg:psql -c "drop table alembic_version" -a my-dribdat-instance`

# Credits

See [Contributors](https://github.com/dataletsch/dribdat/graphs/contributors) for a list of people who have made changes to the code, and [Forks](https://github.com/dataletsch/dribdat/network/members) to find some other users of this project.

Mantained by [@loleg](https://github.com/loleg) and [@gonzalocasas](https://github.com/gonzalocasas), with special thanks to the Swiss communities for [Open Data](https://opendata.ch), [Open Networking](https://opennetworkinfrastructure.org/) and [Open Source](https://dinacon.ch) for the many trials and feedbacks. We are also grateful to F. Wieser and M.-C. Gasser at [Swisscom](http://swisscom.com) for conceptual inputs and financial support of the first alpha release of this project.

This code is originally based on Steven Loria's [flask-cookiecutter](https://github.com/sloria/cookiecutter-flask), which we encourage you to use in YOUR next hackathon!

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
