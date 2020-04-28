python manage.py db init 2>&1 >/dev/null
python manage.py db migrate
python manage.py db upgrade
