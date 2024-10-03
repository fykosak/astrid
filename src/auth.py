from functools import wraps
import tomllib
from authlib.oidc.core.claims import hmac
from flask import abort, redirect, request, session, url_for
from authlib.integrations.flask_client import OAuth
from werkzeug.datastructures import Authorization

with open('/data/config/users.toml', 'rb') as file:
    basicAuthUsers = tomllib.load(file)

def isLoggedIn() -> bool:
    return session.get('user') is not None

def loginBasicAuthUser(auth: Authorization) -> None:
    if auth.username not in basicAuthUsers:
        abort(401)

    user = basicAuthUsers[auth.username]
    if auth.password is None or user['password'] is None:
        abort(401)

    # compare passwords safely
    if not hmac.compare_digest(auth.password, user['password']):
        abort(401)

    if user['roles'] is None:
        raise ValueError(f'User {auth.username} is missing field `roles` in configuration.')

    if not isinstance(user['roles'], list) or not all(isinstance(role, str) for role in user['roles']):
        raise TypeError(f'Config value `roles` must be a list of strings in basic auth user {auth.username}')

    session['user'] = {
        'name': auth.username,
        'realm_access': {
            'roles': user['roles']
        }
    }

def requireLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isLoggedIn():
            # basic auth
            auth = request.authorization
            if auth is not None:
                loginBasicAuthUser(auth)
            else:
                # redirect to oauth
                session['next'] = request.url
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#
# Add all routes needed for auth to passed app
#
# This is a workaround, because app variable is needed for oauth variable,
# which is then used in routes. Flask blueprints cannot be used because it
# would create circular import dependency with app.py.
#
def registerAuthRoutes(app):
    oauth = OAuth(app)
    oauth.register(
        name='keycloak',
        client_id=app.config['OAUTH']['CLIENT_ID'],
        client_secret=app.config['OAUTH']['CLIENT_SECRET'],
        server_metadata_url=app.config['OAUTH']['SERVER_METADATA_URL'],
        client_kwargs={
            'scope': 'openid profile roles'
        }
    )

    @app.route('/login')
    def login():
        redirect_uri = url_for('auth', _external=True)
        return oauth.keycloak.authorize_redirect(redirect_uri)

    @app.route('/auth')
    def auth():
        token = oauth.keycloak.authorize_access_token()
        session['user'] = token['userinfo']
        next_url = session.pop('next', None)
        return redirect(next_url or url_for('index'))

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect('/')
