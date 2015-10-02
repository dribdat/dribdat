deploy: pip install psycopg2
web: gunicorn dribdat.app:create_app\(\) -b 0.0.0.0:$PORT -w 3 --log-file=-
init: python manage.py db init
migrate: python manage.py db migrate
upgrade: python manage.py db upgrade
