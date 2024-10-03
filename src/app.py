from datetime import datetime
from flask import Flask, abort, redirect, render_template, send_from_directory, session, url_for
import os
import tomllib

from repository import Repository
from auth import isLoggedIn, registerAuthRoutes, requireLogin

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# load config
app.config.from_file("/data/config/config.toml", load=tomllib.load, text=False)

registerAuthRoutes(app)

# load repos
with open('/data/config/repos.toml', 'rb') as file:
    reposConfig = tomllib.load(file)

repos = {repo: Repository(repo, '/data/repos/', reposConfig[repo]) for repo in reposConfig}

# automatically inject user to every rendered template
@app.context_processor
def inject_user():
    return dict(user = session.get('user'))

def human_readable_size(size):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            value = f"{size:.2f}".rstrip('0').rstrip('.')
            return f"{value} {unit}"
        size /= 1024.0

#
# routes
#

@app.route('/')
def index():
    if isLoggedIn():
        return render_template('index.html.jinja', repos=repos)
    return render_template('signin.html.jinja')

@app.route('/info/<string:repoName>')
@requireLogin
def info(repoName):
    if repoName not in repos:
        abort(404)
    repo = repos[repoName]
    if not repo.checkAccess():
        abort(401)
    return render_template('info.html.jinja', repo=repoName, log=repo.logger.getLogs())

@app.route('/buildlog/<string:repoName>')
@requireLogin
def buildLog(repoName):
    if repoName not in repos:
        abort(404)
    repo = repos[repoName]
    if not repo.checkAccess():
        abort(401)
    return render_template('buildlog.html.jinja', repo=repoName, log=repo.logger.getBuildLog())

@app.route('/build/<string:repoName>')
@requireLogin
def build(repoName):
    if repoName not in repos:
        abort(404)
    repo = repos[repoName]
    if not repo.checkAccess():
        abort(401)

    repo.execute()

    return redirect(url_for('index'))

# TODO redirect to url with trailing / when showing folder for correct html hrefs
@app.route('/<string:repoName>/')
@app.route('/<string:repoName>/<path:path>')
@requireLogin
def repository(repoName, path=''):
    if repoName not in repos:
        abort(404)
    repo = repos[repoName]
    if not repo.checkAccess():
        abort(401)

    repoDir = os.path.normpath(os.path.join('/data/repos', repoName))
    normalizedPath = os.path.normpath(path)
    targetPath = os.path.normpath(os.path.join(repoDir, normalizedPath))

    # check that listed directory is child of repository directory
    # for potencial directory travelsal attacks
    if not targetPath.startswith(repoDir):
        abort(404)

    if not os.path.exists(targetPath):
        abort(404)

    if (path != '' and os.path.isdir(targetPath) and path[-1] != '/'):
        return redirect(url_for('repository', repoName = repoName, path=path+'/'))

    if os.path.isdir(targetPath):
        directoryContent = next(os.walk(targetPath))
        # filter directories and files starting with .
        dirNames=[d for d in sorted(directoryContent[1]) if not d.startswith('.')]
        fileNames=[f for f in sorted(directoryContent[2]) if not f.startswith('.')]

        # get file metadata
        dirs = []
        for dirName in dirNames:
            filepath = os.path.join(targetPath, dirName)
            modifiedTime = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(' ', timespec='seconds')
            dirs.append([
                dirName, '-', modifiedTime
            ])

        files = []
        for fileName in fileNames:
            filepath = os.path.join(targetPath, fileName)
            size = human_readable_size(os.path.getsize(filepath))
            modifiedTime = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(' ', timespec='seconds')
            files.append([
                fileName, size, modifiedTime
            ])

        return render_template('listdir.html.jinja', path=os.path.normpath(os.path.join(repoName, normalizedPath)), repo=repoName, dirs=dirs, files=files)

    if os.path.isfile(targetPath):
        return send_from_directory(repoDir, normalizedPath)

    abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
