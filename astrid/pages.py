import cherrypy
import os.path
import os
import subprocess
import shlex
import threading
import sys
import time

from git import Repo, Git, GitCommandError
from ConfigParser import ConfigParser

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
                        msg = """#%s Build succeeded.""" % repo.head.commit.hexsha[0:6]
                        msg_class = "green"
                        time_end = time.time()
                    else:
                        msg = """#%s Build failed.""" % repo.head.commit.hexsha[0:6]
                        msg_class = "red"
                except:
                    msg = """#%s Build error.""" % repo.head.commit.hexsha[0:6]
                    msg_class = "red"
                    raise
            except GitCommandError as e:
                msg = "Pull error. (" + str(e) + ")"
                msg_class = "red"
                sendMail = True
                raise
            
            if time_end != None:
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
            g = Git()
            g.clone(remotepath, localpath)

            repo = Repo(localpath)

            if submodules:
                repo.git.submodule("init")

            # not-working umask workaround
            p = subprocess.Popen(["chmod", "g+w", localpath])
            p.wait()        
        else:
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

        # now set correct group (same as build user)
        usr = self.repos.get(reponame, "build_usr")
        p = subprocess.Popen(["chgrp", usr, "-R", localpath])
        p.wait()        

        return repo
        
    def _build(self, reponame):
        usr = self.repos.get(reponame, "build_usr")
        cmd = self.repos.get(reponame, "build_cmd")
        args = self.repos.get(reponame, "build_args")
        cwd = os.path.join(self.repodir, reponame)
        
        logfilename = os.path.expanduser("~/.astrid/%s.build.log" % reponame)
        logfile = open(logfilename, "w")
        p = subprocess.Popen(["sudo", "-u", usr, cmd] + shlex.split(args), cwd=cwd, stdout=logfile, stderr=logfile, stdin=open("/dev/null"))
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
        first = True
        for record in logger.getLogs(reponame):
            record += ['']*(3-len(record))
            if first:
                msg += """<tr><td>%s</td><td><a href="../buildlog/%s">%s</a></td><td>%s</td></tr>""" % (record[0], reponame, record[1],record[2],)
                first = False
            else:
                msg += """<tr><td>%s</td><td>%s</td><td>%s</td></tr>""" % (record[0], record[1],record[2],)
            
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
#                  'tools.staticdir.index' : 'index.html',
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
                repos += """<li><a href="%s">%s</a> (<a href="info/%s">info</a>%s)</li>""" % (section, section, section,building,)
                
        template.assignData("pagetitle", "Astrid")
        template.assignData("repos", repos)
        template.assignData("user", user)
        return template.render()
        

    index._cp_config = {'tools.staticdir.on': False}







