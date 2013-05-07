import cherrypy
import os.path
import os
import subprocess
import shlex
import threading
import sys

from git import Repo, Git
from ConfigParser import ConfigParser

from astrid import BuildLogger
from astrid.templating import Template
import astrid.server

class BasePage(object):
    def __init__(self, repodir, repos):
        self.repos = repos
        self.repodir = repodir
    
    def _checkAccess(self, reponame):
        user = cherrypy.request.login
        if user not in self.repos.get(reponame, "users"):
            raise cherrypy.HTTPError(401)
        

class BuilderPage(BasePage):
    lock = threading.Lock()
    
    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)
        
        self._checkAccess(reponame)
        
        BuilderPage.lock.acquire() # TODO design to lock only manipulated repository
        try:            
            try:
                repo = self._updateRepo(reponame)
                try:
                    if self._build(reponame):
                        msg = """#%s Build succeeded.""" % repo.head.commit.hexsha[0:6]
                        msg_class = "green"
                    else:
                        msg = """#%s Build failed.""" % repo.head.commit.hexsha[0:6]
                        msg_class = "red"
                except:
                    msg = """#%s Build error.""" % repo.head.commit.hexsha[0:6]
                    msg_class = "red"
                    raise
            except:
                msg = "Pull error."
                msg_class = "red"
                raise
            
            
            logger = BuildLogger(self.repodir)
            logger.log(reponame, msg)
            
            template = Template("templates/build.html")
            template.assignData("reponame", reponame)
            template.assignData("message", msg)
            template.assignData("msg_class", msg_class)
            template.assignData("pagetitle", "Build")
            return template.render()
        finally:
            BuilderPage.lock.release()            
    
    def _updateRepo(self, reponame):
        remotepath = self.repos.get(reponame, "path")
        localpath = os.path.join(self.repodir, reponame)
        if not os.path.isdir(localpath):
            g = Git()
            g.clone(remotepath, localpath)
            repo = Repo(localpath)
        else:
            repo = Repo(localpath)
            repo.head.reset(index=True, working_tree=True)
            repo.git.clean("-f")
            repo.remotes.origin.pull()
        return repo
        
    def _build(self, reponame):
        usr = self.repos.get(reponame, "build_usr")
        cmd = self.repos.get(reponame, "build_cmd")
        args = self.repos.get(reponame, "build_args")
        cwd = os.path.join(self.repodir, reponame)
        
        logfile = open("/tmp/astrid.%s.build.log" % reponame, "w")
        p = subprocess.Popen(["sudo", "-u", usr, cmd] + shlex.split(args), cwd=cwd, stdout=logfile, stderr=logfile)
        p.wait()        
        return p.returncode == 0
        
class InfoPage(BasePage):

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)
        
        self._checkAccess(reponame)
        
        logger = BuildLogger(self.repodir)
        
        msg = "<table><tr><th>Time</th><th>Message</th><th>User</th></tr>"
        for record in logger.getLogs(reponame):
            record += ['']*(3-len(record))
            msg += """<tr><td>%s</td><td>%s</td><td>%s</td></tr>""" % (record[0], record[1],record[2],)
        msg += "</table>"
        
        template = Template("templates/info.html")
        template.assignData("reponame", reponame)
        template.assignData("messages", msg)        
        template.assignData("pagetitle", reponame + " info")
        
        return template.render()

class DashboardPage(object):
    _cp_config = {'tools.staticdir.on' : True,
                  'tools.staticdir.dir' : cherrypy.config.get("repodir"),
                  'tools.staticdir.indexlister': astrid.server.htmldir,
#                  'tools.staticdir.index' : 'index.html',
    }
    
    def __init__(self, repos):
        self.repos = repos


    @cherrypy.expose
    def index(self, **params):
        template = Template('templates/home.html')
        repos = ""
        user = cherrypy.request.login

        for section in self.repos.sections():
            if user in self.repos.get(section, "users").split(","):
                repos += """<li><a href="%s">%s</a> (<a href="info/%s">info</a>)</li>""" % (section, section, section,)
                
        template.assignData("pagetitle", "Astrid")
        template.assignData("repos", repos)
        template.assignData("user", user)
        return template.render()
        

    index._cp_config = {'tools.staticdir.on': False}








