from os import environ as os_env

forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

port = str(os_env.get('PORT', 5000))
bind = ['0.0.0.0:%s' % port]
# doesn't work inside docker: '[::1]:%s' % port]

worker_class = 'gevent'
workers = os_env.get('WORKERS', 2)
errorlog = '-'
