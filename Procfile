web: gunicorn dribdat.app:init_app\(\) -b 0.0.0.0:$PORT -w 3 --log-file=-
release: python manage.py db upgrade
