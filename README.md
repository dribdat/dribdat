# Dribdat

[![Travis](https://travis-ci.org/datalets/dribdat.svg?branch=master)](https://travis-ci.org/datalets/dribdat)
[![Coveralls](https://coveralls.io/repos/github/datalets/dribdat/badge.svg?branch=master)](https://coveralls.io/github/datalets/dribdat?branch=master)
[![Gitter](https://img.shields.io/gitter/room/datalets/chat.svg)](https://gitter.im/datalets/chat)

An open platform for data-driven team collaboration, such as *Hackathons*.

This project is being developed by [Datalets](https://datalets.ch), a small studio in Bern, with support from the Swiss open data and open source community. If you need help or advice in setting up your event, or would like to contribute to the project: **get in touch** via our public [Gitter chat](https://gitter.im/datalets/chat) and [GitHub Issues](https://github.com/datalets/dribdat/issues). For more background and references, see [ABOUT](ABOUT.md).

## How does it look?

_Dribdat_ works as a website and project board for running exciting, productive events, and allows organizers and participants to collect their project details in one place, displaying the challenges and projects in Web dashboards, and plugging in community tools such as [Discourse](https://www.discourse.org/), [Slack](http://slack.com), or [Let's Chat](http://sdelements.github.io/lets-chat/) - or using the [remote API](#api) for additional interfaces such as [chatbots](https://github.com/schoolofdata-ch/sodabot) to enhance the hackathon.

Logged-in users can submit challenges, ideas and projects by linking their document or repository, or entering details directly into a form. You can change or customize these [instructions](dribdat/templates/quickstart.html) as you see fit.

![](dribdat/static/img/screenshot_start.png)

Data on projects can be entered into the application directly using [Markdown](https://www.markdowntutorial.com/) formatting, or aggregated simply by putting in a URL to a public project hosted on one of these supported platforms:

- [GitHub](https://github.com) (README / README.md)
- [GitLab](https://gitlab.com) (README.md)
- [BitBucket](https://bitbucket.org) 
- [Etherpad Lite](http://etherpad.org)
- [Google Docs](https://support.google.com/docs/answer/183965?co=GENIE.Platform%3DDesktop&hl=en) (Publish to Web)
- [DokuWiki](http://make.opendata.ch/wiki/project:home)

The administrative interface shown below allows defining details of the event and managing project data.

![](dribdat/static/img/screenshot_admin_projects.png)

The look and feel of the project view can be customized with CSS, and shows challenges and projects, with a rating of how completely they are documented. In the `Events` screen there are links to a *Print* view for a summary of all projects on one page, and the ability to *Embed* results into another website.

![](dribdat/static/img/screenshot_makezurich.jpg)

And, as we're really into making the most of those time constraints, the homepage and dashboard feature a big animated countdown clock.

![](dribdat/static/img/screenshot_countdown.png)

Tick tock!

## Deployment Quickstart

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

OAuth 2.0 support is built in, currently fully supporting Slack, using these variables:

* `DRIBDAT_SLACK_ID` - an OAuth Client ID to enable [Sign in with Slack](https://api.slack.com/docs/sign-in-with-slack)
* `DRIBDAT_SLACK_SECRET` - ..and client secret.

Set the redirect URL in your app's OAuth Settings to `<SERVER_URL>/slack_callback`

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

Install Python, Virtualenv and Pip or Pipenv to start working with the code.

You may need to install additional libraries (`libffi`) for the [misaka](http://misaka.61924.nl/) package, which depends on [CFFI](https://cffi.readthedocs.io/en/latest/installation.html#platform-specific-instructions), e.g. `sudo dnf install libffi-devel`

Run the following commands to bootstrap your environment.

```
git clone https://github.com/datalets/dribdat
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

## Credits

Developed by [Oleg Lavrovsky](http://datalets.ch) based on Steven Loria's [flask-cookiecutter](https://github.com/sloria/cookiecutter-flask). With thanks to the Swiss communities for [Open Data](https://opendata.ch), [Open Networking](https://opennetworkinfrastructure.org/) and [Open Source](https://dinacon.ch) for their many contributions, and to [Swisscom](http://swisscom.com) via F. Wieser and M.-C. Gasser for conceptual inputs and financial support of the first release of this project.
