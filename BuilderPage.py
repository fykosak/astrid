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

import sys

class BuilderPage(object):
    lock = threading.Lock()
    
    def __init__(self, repodir, repos):
        self.repos = repos
        self.repodir = repodir

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)
        
        BuilderPage.lock.acquire() # TODO design to lock only manipulated repository
        try:            
            try:
                return self._updateRepo(reponame)
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
            except:
                msg = "Pull error." 
                msg_class = "red"
                #raise
            
            
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
        return localpath + ", " remotepath
        if not os.path.isdir(localpath):
            g = Git()
            g.clone(remotepath, localpath)
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
        
