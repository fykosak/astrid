import cherrypy
import os.path
import os
import subprocess
import shlex
import threading

from git import Repo, Git
from ConfigParser import ConfigParser

from BuildLogger import BuildLogger
from Template import Template


class BuilderPage(object):
    lock = threading.Lock()
    
    def __init__(self, repodir):
        self.repos = ConfigParser()
        self.repos.read('repos.ini')
        self.repodir = repodir

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)
        
        BuilderPage.lock.acquire() # TODO design to lock only manipulated repository
        try:            
            try:
                repo = self._updateRepo(reponame)
            except:
                msg = "Pull error."
                msg_class = "red"
            
            try:
                print "pulled: " + repo.head.commit.hexsha
                if self._build(reponame):
                    msg = "Build succeeded."
                    msg_class = "green"
                else:
                    msg = "Build failed."
                    msg_class = "red"
            except:
                msg = "Build error."
                msg_class = "red"
            
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
            os.mkdir(localpath)
            Repo.clone_from(remotepath, localpath)
            repo = Repo(localpath)
        else:
            repo = Repo(localpath)
            repo.remotes.origin.pull()
        return repo
        
    def _build(self, reponame):
        cmd = self.repos.get(reponame, "build_cmd")
        args = self.repos.get(reponame, "build_args")
        cwd = os.path.join(self.repodir, reponame)
        
        p = subprocess.Popen([cmd] + shlex.split(args), cwd=cwd)
        p.wait()        
        return p.returncode == 0
        