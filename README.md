# DRIBDAT

*This is an open Hackathon. The stakes are high, the competition is ready. You will be measured, your progress tracked, your creativity analysed & compared. Think you have what it takes? Ready, steady, go!*

**DRIBDAT (Driven By Data) is an open platform for data-driven hackathons.** It works as a website and project board for running exciting, productive Hackathons..with Impact Factor. We created this after running events using plain wikis and forums for years, and trying out a few proprietary tools that we felt limited us in one way or another.

See [DRIBD.AT](http://dribd.at) for more information.

## Deployment

Instructions to set up a development instance of this platform follow. This project is ready for fast deployment to [Heroku](http://heroku.com). You will need to set the following configuration variables:

* `SERVER_URL` - fully qualified domain name where the site is hosted, e.g. minotaur-realm-1234.herokuapp.com or your custom domain name
* `DRIBDAT_ENV` - 'dev' to enable debugging, 'prod' to optimise assets etc.
* `DRIBDAT_DB` - if you are using the Postgres add-on, this would be postgres://username:password@...
* `DATABASE_URL` - same as above - needed only for Heroku to recognise the database, set automatically if you use tools
* `DRIBDAT_SECRET` - a long scary string for hashing your passwords

We have used [OpBeat](https://opbeat.com/) and their new Flask metrics to track performance and logging. If you would like to enable this, set these as per their documentation:

* `OPBEAT_APP_ID`
* `OPBEAT_ORGANIZATION_ID`
* `OPBEAT_SECRET_TOKEN`

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

Once you have installed your DBMS, run the following to create your app's database tables and perform the initial migration:

```
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
python manage.py server
```

## Deployment

In your production environment, make sure the `DRIBDAT_ENV` environment variable is set to `prod`.

### Shell

To open the interactive shell, run: `python manage.py shell`

By default, you will have access to `app`, `db`, and the `User` model.

For example, to make yourself Administrator, create a user through the frontend, then:

```
u = User.query.first()
u.is_admin = True
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

Developed by [Oleg Lavrovsky](http://github.com/loleg) based on [Steven Loria](http://github.com/sloria/)'s [cookiecutter](http://github.com/audreyr/cookiecutter/) template.

With thanks to [Swisscom](http://swisscom.com)'s F. Wieser and M.-C. Gasser for conceptual inputs and financial support of the first release of this project.
