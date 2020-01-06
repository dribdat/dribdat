web: gunicorn dribdat.app:init_app\(\) -b 0.0.0.0:$PORT -w 3 --log-file=-
init: python manage.py db init
migrate: python manage.py db migrate
release: yarn && python manage.py db upgrade
