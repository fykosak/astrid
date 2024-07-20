from functools import wraps
from flask import redirect, request, session, url_for
from authlib.integrations.flask_client import OAuth

def isLoggedIn() -> bool:
    return 'user' in session and session['user'] is not None

def requireLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isLoggedIn():
            print(request.url)
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
