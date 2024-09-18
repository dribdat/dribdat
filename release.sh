#!/bin/bash
# Release script

# set APPDIR if running from a different directory, e.g. in container

if [ "$FORCE_MIGRATE" ]; then
	# Forced upgrade
	"${APPDIR:-.}/force-migrate.sh" psql

else
	# Standard upgrade
	python "${APPDIR:-.}/manage.py" db upgrade 2>&1 >/dev/null
fi

# Compress assets
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/js"
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/css"
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/img"
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/public"
