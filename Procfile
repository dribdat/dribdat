web: gunicorn dribdat.app:init_app\(\) -b 0.0.0.0:$PORT -w 3 --log-file=-
release: ./upgrade.sh && npm i
