web: gunicorn --config=gunicorn.conf.py dribdat.app:init_app\(\)
default: gunicorn dribdat.app:init_app\(\) -b 0.0.0.0:$DEFAULT_PORT -w 3 --log-file=-
release: ./release.sh
