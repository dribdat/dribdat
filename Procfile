web: gunicorn dribdat.app:init_app\(\) -b 0.0.0.0:$PORT -w 3 --log-file=-
eventlet: gunicorn --config=gunicorn.conf.py dribdat.app:init_app\(\)
release: ./release.sh
