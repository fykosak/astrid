import cherrypy
import os.path
import os

from ConfigParser import ConfigParser

from BuildLogger import BuildLogger
from Template import Template


class InfoPage(object):
    def __init__(self, repodir):
        self.repos = ConfigParser()
        self.repos.read('repos.ini')
        self.repodir = repodir

    @cherrypy.expose
    def default(self, reponame):
        if reponame not in self.repos.sections():
            raise cherrypy.HTTPError(404)
        
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
        
