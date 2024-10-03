import tomllib

def get_config():
    with open('/data/config/config.toml', 'rb') as file:
        return tomllib.load(file)

wsgi_app = 'app:app'
bind = "0.0.0.0:8080"
preload_app = True # must be set for locks to work between different gunicorn workers

workers = get_config()['GUNICORN']['WORKERS']
threads = get_config()['GUNICORN']['THREADS']
