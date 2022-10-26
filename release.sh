#!/bin/bash
# Release script

if [ "$FORCE_MIGRATE" ]; then
	./force-migrate.sh psql

else
	# Silent upgrade
	python manage.py db upgrade 2>&1 >/dev/null
fi

# Compress assets
python -m whitenoise.compress dribdat/static/js
python -m whitenoise.compress dribdat/static/css
python -m whitenoise.compress dribdat/static/img
python -m whitenoise.compress dribdat/static/public
