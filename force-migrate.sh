#!/bin/bash
if [ "$1" = "heroku" ]; then
	if [ -z "$2" ]; then
		echo "Specify the app you wish to upgrade as a second parameter."
		exit
	fi
	echo "Migrating Heroku DB on $2 in 5 seconds - Ctrl-C to abort."
	sleep 5s
	heroku pg:psql -a $2 -c "drop table alembic_version"
	heroku run -a $2 "python manage.py db init && python manage.py db migrate && python manage.py db upgrade"
else
	echo "Resetting local DB in 5 seconds - Ctrl-C to abort."
	echo "(Use 'heroku' argument to migrate Heroku instance)"
	sleep 5s
	rm -rf dev.db migrations
	python manage.py db init
	python manage.py db migrate
	python manage.py db upgrade
fi
