#!/bin/bash
# Run without arguments or scroll down for instructions

if [ "$1" = "psql" ]; then
	echo "Force migrating database"
	rm -rf migrations/
	psql -c "DROP TABLE alembic_version;" $DATABASE_URL
	python "${APPDIR:-.}/manage.py" db init 2>&1 >/dev/null
	python "${APPDIR:-.}/manage.py" db migrate
	python "${APPDIR:-.}/manage.py" db upgrade
	echo "Upgrade complete, 10 second cooldown"
	sleep 10

elif [ "$1" = "heroku" ]; then
	if [ -z "$2" ]; then
		echo "Specify the app you wish to upgrade as a second parameter."
		exit
	fi
	echo "Migrating Heroku DB on $2 in 5 seconds - Ctrl-C to abort."
	sleep 5s
	heroku pg:psql -a $2 -c "drop table alembic_version"
	heroku run -a $2 "python ${APPDIR:-.}/manage.py db init && python ${APPDIR:-.}/manage.py db migrate && python ${APPDIR:-.}/manage.py db upgrade"

elif [ "$1" = "local" ]; then
	echo "Resetting local SQLite DB (dev.db)"
	rm -rf "${APPDIR:-.}/dev.db"
	python "${APPDIR:-.}/manage.py" db migrate
	python "${APPDIR:-.}/manage.py" db upgrade

else
	echo "Use this script with the following arguments to refresh the DB schema:"
	echo " psql - in production (such as your server ssh console)"
	echo " heroku - to modify a locally configured remote app"
	echo " local - wipe and reset your development SQLite file (dev.db)"
fi
