import os.path
import os
import subprocess
import time
import cherrypy

from git import Repo, Git, GitCommandError

from astrid import BuildLogger
from astrid.templating import Template
import astrid.server

class BasePage(object):
    def __init__(self, repodir, repos, locks):
        self.repos = repos
        self.repodir = repodir
        self.locks = locks

    def _checkAccess(self, reponame):
        user = cherrypy.request.login
        if user not in self.repos.get(reponame, "users"):
            raise cherrypy.HTTPError(401)

    def _isBuilding(self, reponame):
        lock = self.locks[reponame]
        building = not lock.acquire(False)
        if not building: # repo's not building, we release the lock
            lock.release()
        return building


class BuilderPage(BasePage):

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)

        self._checkAccess(reponame)
        lock = self.locks[reponame]
        msg = None
        sendMail = False

        lock.acquire()
        try:
            try:
                time_start = time.time()
                time_end = None
                repo = self._updateRepo(reponame)
                try:
                    if self._build(reponame):
                        msg = f"#{repo.head.commit.hexsha[0:6]} Build succeeded."
                        msg_class = "green"
                        time_end = time.time()
                    else:
                        msg = f"#{repo.head.commit.hexsha[0:6]} Build failed."
                        msg_class = "red"
                        time_end = time.time()
                except:
                    msg = f"#{repo.head.commit.hexsha[0:6]} Build error."
                    msg_class = "red"
                    raise
            except GitCommandError as e:
                msg = f"Pull error. ({e})"
                msg_class = "red"
                sendMail = True
                raise

            if time_end is not None:
                msg += " ({:.2f} s)".format(time_end - time_start)

            template = Template("templates/build.html")
            template.assignData("reponame", reponame)
            template.assignData("message", msg)
            template.assignData("msg_class", msg_class)
            template.assignData("pagetitle", "Build")
            return template.render()
        finally:
            logger = BuildLogger(self.repodir)
            logger.log(reponame, msg, sendMail)
            lock.release()

    def _updateRepo(self, reponame):
        remotepath = self.repos.get(reponame, "path")
        submodules = self.repos.get(reponame, "submodules") if self.repos.has_option(reponame, "submodules") else False
        localpath = os.path.join(self.repodir, reponame)

        os.umask(0o007) # create repo content not readable to others
        if not os.path.isdir(localpath):
            print(f"Repository {reponame} empty, cloning")
            g = Git()
            g.clone(remotepath, localpath)

            repo = Repo(localpath)

            if submodules:
                repo.git.submodule("init")

            # not-working umask workaround
            subprocess.run(["chmod", "g+w", localpath], check=False)
        else:
            print(f"Pulling repository {reponame}")
            repo = Repo(localpath)
            try:
                repo.git.update_index("--refresh")
            except GitCommandError:
                pass # it's fine, we'll reset
            # We use wrapped API (direct git command calls) rather than calling semantic GitPython API.
            # (e.g. repo.remotes.origin.pull() was replaced by repo.git.pull("origin"))
            repo.git.reset("--hard", "master")
            #repo.git.clean("-f")
            repo.git.pull("origin")

            if submodules:
                repo.git.submodule("init")
                repo.git.submodule("foreach", "git", "fetch")
                repo.git.submodule("update")

        return repo

    def _build(self, reponame):
        cmd = self.repos.get(reponame, "build_cmd")
        cwd = os.path.join(self.repodir, reponame) # current working directory
        image_version = self.repos.get(reponame, "image_version")

        print(f"Building {reponame}")
        logfilename = os.path.expanduser(f"/data/log/{reponame}.build.log")
        logfile = open(logfilename, "w")
        p = subprocess.run(["docker", "run", "--rm", "-v", f"{cwd}:/usr/src/local", f"--user={os.getuid()}",  f"fykosak/buildtools:{image_version}"] + cmd.split(), cwd=cwd, stdout=logfile, stderr=logfile, check=False)
        logfile.close()
        return p.returncode == 0

class InfoPage(BasePage):

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)

        self._checkAccess(reponame)

        logger = BuildLogger(self.repodir)

        msg = "<table><tr><th>Time</th><th>Message</th><th>User</th></tr>"
        first = True
        for record in logger.getLogs(reponame):
            record += ['']*(3-len(record))
            if first:
                msg += f'<tr><td>{record[0]}</td><td><a href="../buildlog/{reponame}">{record[1]}</a></td><td>{record[2]}</td></tr>'
                first = False
            else:
                msg += f"<tr><td>{record[0]}</td><td>{record[1]}</td><td>{record[2]}</td></tr>"

        msg += "</table>"

        template = Template("templates/info.html")
        template.assignData("reponame", reponame)
        for k, v in self.repos.items(reponame):
            template.assignData("repo." + k, v)

        template.assignData("messages", msg)
        template.assignData("pagetitle", reponame + " info")

        return template.render()

class BuildlogPage(BasePage):

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)

        self._checkAccess(reponame)

        logger = BuildLogger(self.repodir)
        building = self._isBuilding(reponame)
        building = ', building&hellip;' if building else ''

        template = Template("templates/buildlog.html")
        template.assignData("reponame", reponame)
        template.assignData("building", building)
        template.assignData("buildlog", logger.getBuildlog(reponame))

        template.assignData("pagetitle", reponame + " build log")

        return template.render()


class DashboardPage(BasePage):
    _cp_config = {'tools.staticdir.on' : True,
                  'tools.staticdir.dir' : cherrypy.config.get("repodir"),
                  'tools.staticdir.indexlister': astrid.server.htmldir,
                  'tools.staticdir.content_types': {
                      'aux': 'text/plain; charset=utf-8',
                      'log': 'text/plain; charset=utf-8',
                      'toc': 'text/plain; charset=utf-8',
                      'out': 'text/plain; charset=utf-8',
                      'tex': 'text/plain; charset=utf-8',
                      'mpx': 'text/plain; charset=utf-8',
                      'mp': 'text/plain; charset=utf-8',
                      'plt': 'text/plain; charset=utf-8',
                      'dat': 'text/plain; charset=utf-8',
                      'csv': 'text/csv; charset=utf-8',
                      'py': 'text/x-python; charset=utf-8',
                      'sh': 'text/x-sh; charset=utf-8',
                      'soap': 'application/soap+xml',
                      'ipe': 'application/xml'
                      #'inc': ??? or download like .tex
                      #'sample': ??? how about this stuff?
                      #'Makefile': ??? how about Makefiles
                   }
                   #'tools.staticdir.index' : 'index.html',
    }

    @cherrypy.expose
    def index(self, **params):
        template = Template('templates/home.html')
        repos = ""
        user = cherrypy.request.login

        for section in self.repos.sections():
            if user in self.repos.get(section, "users").split(","):
                building = self._isBuilding(section)
                building = ', building&hellip;' if building else ''
                repos += f'<li><a href="{section}">{section}</a> (<a href="info/{section}">info</a>{building})</li>'

        template.assignData("pagetitle", "Astrid")
        template.assignData("repos", repos)
        template.assignData("user", user)
        return template.render()

    index._cp_config = {'tools.staticdir.on': False}
