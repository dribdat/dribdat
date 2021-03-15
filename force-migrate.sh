#!/bin/bash
# Run without arguments or scroll down for instructions

if [ "$1" = "psql" ]; then
	echo "Force migrating database"
	rm -rf migrations/
	psql -c "DROP TABLE alembic_version;" $DATABASE_URL
	python manage.py db init 2>&1 >/dev/null
	python manage.py db migrate
	python manage.py db upgrade
	sleep 2
	echo "Upgrade complete"

elif [ "$1" = "heroku" ]; then
	if [ -z "$2" ]; then
		echo "Specify the app you wish to upgrade as a second parameter."
		exit
	fi
	echo "Migrating Heroku DB on $2 in 5 seconds - Ctrl-C to abort."
	sleep 5s
	heroku pg:psql -a $2 -c "drop table alembic_version"
	heroku run -a $2 "python manage.py db init && python manage.py db migrate && python manage.py db upgrade"

elif [ "$1" = "local" ]; then
	echo "Resetting local SQLite DB (dev.db)"
	rm -rf dev.db migrations
	python manage.py db init
	python manage.py db migrate
	python manage.py db upgrade

else
	echo "Use this script to refresh the DB schema:"
	echo "- in production (such as Heroku console), with the psql argument"
	echo "- use the heroku argument to modify a locally configured remote app"
	echo "- without arguments, it will ask you if you want to reset your SQLite DB"
fi
