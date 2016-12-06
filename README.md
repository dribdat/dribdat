# Dribdat

*The stakes are high, the competition is ready. You will be measured, your progress tracked, your creativity analysed & compared. Think you have what it takes? Ready, steady, go!*

**Dribdat (from "Driven By Data") is an open platform for data-driven team collaboration, such as Hackathons.** It works as a website and project board for running exciting, productive events..with Impact Factor. We created this after using plain wikis and forums for years, and trying out a few proprietary tools that we felt limited us in one way or another.

[Visit this page](https://datalets.ch/dribdat/iot-2015/project/23/) for more background.

## Deployment Quickstart

Instructions to set up a development instance of this platform follow. This project is ready for fast deployment to [Heroku](http://heroku.com):

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

You can set the following configuration variables:

* `SERVER_URL` - fully qualified domain name where the site is hosted
* `DRIBDAT_ENV` - 'dev' to enable debugging, 'prod' to optimise assets etc.
* `DRIBDAT_APIKEY` - for connecting clients to the remote API (WIP)
* `DATABASE_URL` - if you are using the Postgres add-on, this would be postgres://username:password@... - in Heroku this is set automatically
* `DRIBDAT_SECRET` - a long scary string for hashing your passwords - in Heroku this is set automatically

Once your app is deployed on Heroku, create a user and use the shell commands below to become an administrator.

## Developer Quickstart

First, set your app's secret key as an environment variable. For example, example add the following to `.bashrc` or `.bash_profile`.

```
export DRIBDAT_SECRET='something-really-secret'
```

Then run the following commands to bootstrap your environment.

```
git clone https://github.com/loleg/dribdat
cd dribdat
pip install -r requirements/dev.txt
python manage.py server
```

You will see a pretty welcome screen at http://localhost:5000

The first user that registers becomes an admin, so don't delay!

Once you have installed your DBMS, run the following to create your app's database tables and perform the initial migration:

```
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
python manage.py server
```

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

## API notes

There are a few API calls that admins can use to easily get to the data in Dribdat.

Summary of all projects from current event in CSV or JSON format:
`/admin/event/<EVENT ID>/projects.csv`
`/admin/event/<EVENT ID>/projects.json`

A print view of all projects is also accessible from the Events admin console.

## Credits

Developed by [Oleg Lavrovsky](http://datalets.ch) based on [Steven Loria's flask-cookiecutter](https://github.com/sloria/cookiecutter-flask).

With thanks to [Swisscom](http://swisscom.com)'s F. Wieser and M.-C. Gasser for conceptual inputs and financial support of the first release of this project.
