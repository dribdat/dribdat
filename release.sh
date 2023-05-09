#!/bin/bash
# Release script

# set APPDIR if running from a different directory, e.g. in container

if [ "$FORCE_MIGRATE" ]; then
	"${APPDIR:-.}/force-migrate.sh" psql

else
	# Silent upgrade
	python "${APPDIR:-.}/manage.py" db upgrade 2>&1 >/dev/null
	echo "Warning! Your database may be out of sync due to a forced upgrade."
fi

# Compress assets
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/js"
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/css"
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/img"
python -m whitenoise.compress "${APPDIR:-.}/dribdat/static/public"
