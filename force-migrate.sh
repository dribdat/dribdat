#!/bin/bash
if [ "$1" = "heroku" ]; then
	echo "Migrating Heroku DB in 5 seconds - Ctrl-C to abort."
	sleep 5s
	heroku pg:psql -c "drop table alembic_version"
	heroku run "python manage.py db init && python manage.py db migrate && python manage.py db upgrade"
else
	echo "Resetting local DB in 5 seconds - Ctrl-C to abort."
	echo "(Use 'heroku' argument to migrate Heroku instance)"
	sleep 5s
	rm -rf dev.db migrations
	python manage.py db init
	python manage.py db migrate
	python manage.py db upgrade
fi
