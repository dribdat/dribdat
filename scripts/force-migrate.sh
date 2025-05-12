#!/bin/bash
# Run without arguments or scroll down for instructions

if [ -n "$1" ]; then
	echo "This tool attempts to force your $1 database in sync with current Alembic schema."
	echo "Only use in case of problems: use the release.sh script for regular deployments."
	echo "!!!"
	echo "Pausing for 2 seconds - Ctrl-C to abort"; sleep 2s
fi	

if [ "$1" = "psql" ]; then
	echo "Force upgrading Postgres database"
	python "${APPDIR:-.}/manage.py" db stamp --purge
	python "${APPDIR:-.}/manage.py" db upgrade
	echo "Upgrade complete"

elif [ "$1" = "xpsqlx" ]; then
	echo "Resetting migrating and upgrating Postgres database"
	python "${APPDIR:-.}/manage.py" db stamp --purge
	rm -rf migrations
	python "${APPDIR:-.}/manage.py" db init 2>&1 >/dev/null
	python "${APPDIR:-.}/manage.py" db migrate
	python "${APPDIR:-.}/manage.py" db upgrade
	echo "Upgrade complete"

elif [ "$1" = "heroku" ]; then
	if [ -z "$2" ]; then
		echo "Specify the app you wish to upgrade as a second parameter."
		exit
	fi
	echo "Migrating Heroku DB on $2"
	heroku run -a $2 "python ${APPDIR:-.}/manage.py db stamp --purge && python ${APPDIR:-.}/manage.py db upgrade"
	echo "Upgrade complete"

elif [ "$1" = "xherokux" ]; then
	if [ -z "$2" ]; then
		echo "Specify the app you wish to upgrade as a second parameter."
		exit
	fi
	echo "Resetting Heroku DB on $2"
	heroku pg:psql -a $2 -c "drop table alembic_version"
	heroku run -a $2 "python ${APPDIR:-.}/manage.py db init && python ${APPDIR:-.}/manage.py db migrate && python ${APPDIR:-.}/manage.py db upgrade"
	echo "Upgrade complete"

elif [ "$1" = "sqlite" ]; then
	echo "Migrating local SQLite DB (dev.db)"
	python "${APPDIR:-.}/manage.py" db stamp --purge
	python "${APPDIR:-.}/manage.py" db upgrade
	echo "Upgrade complete"

elif [ "$1" = "xsqlitex" ]; then
	echo "Wiping and resetting local SQLite DB (dev.db -> /tmp/dribdat-dev.db)"
	mv "${APPDIR:-.}/dev.db" "/tmp/dribdat-dev.db"
	rm -f "${APPDIR:-.}/dev.db"
	python "${APPDIR:-.}/manage.py" db upgrade
	echo "Upgrade complete"

else
	echo "Use this script with one of the following arguments to refresh your database:"
	echo " psql - Postgres in production (such as your server ssh console)"
	echo " xpsqlx - re-initialize the Postgres database (data loss possible)"
	echo " heroku <app> - to remigrate a locally configured Heroku app"
	echo " xherokux <app> - re-initialize the Heroku database (data loss possible)"
	echo " sqlite - force migrate your development SQLite file (dev.db)"
	echo " xsqlitex - wipe and reset your development SQLite file (data loss)"
fi
