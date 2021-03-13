# Use this script to refresh the DB schema
if [ "$FORCE_MIGRATE" ]; then
	echo "Force migrating database"
	rm -rf migrations/
	psql -c "DROP TABLE alembic_version;" $DATABASE_URL
	python manage.py db init 2>&1 >/dev/null
	python manage.py db migrate
fi
echo "Upgrading database"
python manage.py db upgrade
sleep 2
echo "Upgrade complete"
