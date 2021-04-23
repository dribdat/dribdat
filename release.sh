#!/bin/bash
# Release script

if [ "$FORCE_MIGRATE" ]; then
	./force-migrate.sh psql

else
	# Silent upgrade
	python manage.py db upgrade 2>&1 >/dev/null
fi
