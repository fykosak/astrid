from datetime import datetime
from flask import Flask, abort, redirect, render_template, send_from_directory, session, url_for, request
import os
import tomllib
from functools import wraps
import magic

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

def repo_required(f):
    @wraps(f)
    def decorated_function(repo_name, *args, **kwargs):
        if repo_name not in repos:
            abort(404)
        repo = repos[repo_name]
        if not repo.checkAccess():
            abort(401)
        return f(repo=repo, *args, **kwargs)
    return decorated_function

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
        filtered_repos = {name: repo for name, repo in repos.items() if not repo.config.get('archived', False)}
        return render_template('index.html.jinja', repos=filtered_repos)
    return render_template('signin.html.jinja')

@app.route('/archive')
@requireLogin
def archive():
    if isLoggedIn():
        return render_template('index.html.jinja', repos=repos, archive=True)
    return render_template('signin.html.jinja')

@app.route('/info/<string:repo_name>')
@requireLogin
@repo_required
def info(repo: Repository):
    logs = repo.logger.getLogs()
    formatted_logs = []
    for i, log in enumerate(logs):
        if i < 10:
            commit_hash = log[1].split()[0][1:]
            try:
                commit_msg, commit_author, commit_url = repo.get_commit_info(commit_hash)
                formatted_commit_info = f"<a href='{commit_url}' target='_blank' class='link-pink'>#{commit_hash}</a>: {commit_msg} (by {commit_author})"
            except Exception as e:
                formatted_commit_info = ''
        else:
            formatted_commit_info = ''
        formatted_logs.append((log[0], log[1], log[2], formatted_commit_info))
    
    return render_template('info.html.jinja', repo_name=repo.name, log=formatted_logs)

@app.route('/buildlog/<string:repo_name>')
@requireLogin
@repo_required
def buildlog(repo: Repository):
    return render_template('buildlog.html.jinja', repo_name=repo.name, log=repo.logger.getBuildLog())

@app.route('/build/<string:repo_name>')
@requireLogin
@repo_required
def build(repo: Repository):
    repo.execute()
    return redirect(url_for('index'))

def check_and_parse_path(repo: Repository, path):
    repo_dir = os.path.normpath(os.path.join('/data/repos', repo.name))
    normalized_path = os.path.normpath(path)
    target_path = os.path.normpath(os.path.join(repo_dir, normalized_path))

    # check that listed directory is child of repository directory
    # for potential directory traversal attacks
    if not target_path.startswith(repo_dir):
        abort(404)

    if not os.path.exists(target_path):
        abort(404)

    return repo_dir, normalized_path, target_path

def create_breadcrumbs(repo: Repository, normalized_path):
    path_parts = ["All Repos", repo.name]
    if normalized_path != ".":
        path_parts += normalized_path.split(os.path.sep)
    breadcrumbs = []
    for i, part in enumerate(path_parts):
        if i == 0:
            url = url_for('index')
        else:
            url = url_for('repository', repo_name=repo.name, path=os.path.sep.join(path_parts[2:i+1]))
        breadcrumbs.append({'name': part, 'url': url})
    return breadcrumbs


@app.route('/<string:repo_name>/')
@app.route('/<string:repo_name>/<path:path>')
@requireLogin
@repo_required
def repository(repo: Repository, path=''):
    repo_dir, normalized_path, target_path = check_and_parse_path(repo, path)
    if (path != '' and os.path.isdir(target_path) and path[-1] != '/'):
        return redirect(url_for('repository', repo_name=repo.name, path=path+'/'))

    if os.path.isdir(target_path):
        directory_content = next(os.walk(target_path))
        # filter directories and files starting with .
        dir_names = [d for d in sorted(directory_content[1]) if not d.startswith('.')]
        file_names = [f for f in sorted(directory_content[2]) if not f.startswith('.')]

        # get file metadata
        dirs = []
        for dir_name in dir_names:
            filepath = os.path.join(target_path, dir_name)
            modified_time = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(' ', timespec='seconds')
            dirs.append([
                dir_name, '-', modified_time
            ])

        files = []
        for file_name in file_names:
            filepath = os.path.join(target_path, file_name)
            size = human_readable_size(os.path.getsize(filepath))
            modified_time = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(' ', timespec='seconds')
            files.append([
                file_name, size, modified_time
            ])

        return render_template('listdir.html.jinja', path=os.path.normpath(os.path.join(repo.name, normalized_path)), repo_name=repo.name, dirs=dirs, files=files, breadcrumbs=create_breadcrumbs(repo, normalized_path))

    if os.path.isfile(target_path):
        if request.headers.get('Accept') == '*/*':
            return send_from_directory(repo_dir, normalized_path)
        file_display_type = 'other'
        file_content = None

        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(target_path)
        if detected_mime in ['application/pdf', 'text/xml', "application/json"]:
            return send_from_directory(repo_dir, normalized_path)
        elif detected_mime.startswith('text/'):
            file_display_type = 'text'
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as file:
                file_content = file.read()
        elif detected_mime.startswith('image/'):
            file_display_type = 'image'
        else:
            file_display_type = 'other'
        return render_template('viewfile.html.jinja', 
                               breadcrumbs=create_breadcrumbs(repo, normalized_path),
                               path=normalized_path,
                               repo_name=repo.name, 
                               file_content=file_content,
                               file_display_type=file_display_type)

    abort(404)

@app.route('/download-file/<string:repo_name>/<path:path>')
@requireLogin
@repo_required
def download_file(repo: Repository, path=''):
    repo_dir, normalized_path, target_path = check_and_parse_path(repo, path)
    if os.path.isfile(target_path):
        return send_from_directory(repo_dir, normalized_path)
    abort(404)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
