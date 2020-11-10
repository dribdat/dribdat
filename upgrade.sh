# Use this script to refresh the DB schema
echo "Migrating and upgrating database"
rm -rf migrations/
psql -c "DROP TABLE alembic_version;" $DATABASE_URL
python manage.py db init 2>&1 >/dev/null
python manage.py db migrate
python manage.py db upgrade
echo "Upgrade complete"
sleep 10
