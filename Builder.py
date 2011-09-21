import cherrypy
import os.path
import os
import subprocess
import shlex

from git import Repo, Git
from ConfigParser import ConfigParser


class Builder(object):
    def __init__(self, repodir):
        self.repos = ConfigParser()
        self.repos.read('repos.ini')
        self.repodir = repodir

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)
        try:
            self._updateRepo(reponame)
        except:
            return "Pull error."
        #try:
        print "going building"
        if self._build(reponame):
            return "Build succeeded."
        else:
            return "Build failed."
        #except:
         #   return "Build error."
        
    
    def _updateRepo(self, reponame):
        remotepath = self.repos.get(reponame, "path")
        localpath = os.path.join(self.repodir, reponame)
        if not os.path.isdir(localpath):
            os.mkdir(localpath)
            Repo.clone_from(remotepath, localpath)
        else:
            repo = Repo(localpath)
            repo.remotes.origin.pull()
    
    def _build(self, reponame):
        cmd = self.repos.get(reponame, "build_cmd")
        args = self.repos.get(reponame, "build_args")
        cwd = os.path.join(self.repodir, reponame)
        
        p = subprocess.Popen([cmd] + shlex.split(args), cwd=cwd)
        p.wait()        
        return p.returncode == 0
        