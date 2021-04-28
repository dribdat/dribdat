from os import environ as os_env

forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
bind = '0.0.0.0:%s' % str(os_env.get('PORT', 5000))
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
errorlog = '-'
