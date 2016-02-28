from datetime import datetime
from email.mime.text import MIMEText

import cherrypy
import os.path
import smtplib
import threading

class BuildLogger:
    separator = ";"
    
    def __init__(self, repodir):
        self.repodir = repodir
        
    def _getLogfile(self, reponame):
        return os.path.expanduser('~/.astrid/{}.log'.format(reponame))

    def _getBuildlogfile(self, reponame):
        return os.path.expanduser('~/.astrid/{}.build.log'.format(reponame))
         
    def log(self, reponame, message, sendMail = False):
        logfile = self._getLogfile(reponame)
        f = open(logfile, "a")
        user = cherrypy.request.login
        f.write(BuildLogger.separator.join([datetime.now().isoformat(' '), message, user]) + "\n")
        f.close()
    
        if sendMail:
            self._sendMail(reponame, message)
    
    def getLogs(self, reponame):
        logfile = self._getLogfile(reponame)
        try:
            f = open(logfile, "r")
                
            records = [row.split(BuildLogger.separator) for row in reversed(list(f))]
            f.close()
            return records
        except:
            return []

    def getBuildlog(self, reponame):
        fn = self._getBuildlogfile(reponame)
        try:
            f = open(fn, "r")
            res = f.read()
            f.close()
            return res
        except:
            return None

    def _sendMail(self, reponame, message):
        headerFrom = cherrypy.config.get("mail_from")
        headerTo = cherrypy.config.get("mail_to")

        msg = MIMEText(message)
        msg['Subject'] = 'Astrid coughed on repo %s' % reponame
        msg['From'] = headerFrom
        msg['To'] = headerTo

        try:
            s = smtplib.SMTP('localhost')
            s.sendmail(headerFrom, [headerTo], msg.as_string())
            s.quit()
        except:
            pass


from ConfigParser import ConfigParser

REPOS_INI = '~/.astrid/repos.ini'
CONFIG_INI = '~/.astrid/config.ini'

repos = ConfigParser()
repos.read(os.path.expanduser(REPOS_INI))
cherrypy.engine.autoreload.files.add(REPOS_INI)

config = os.path.expanduser(CONFIG_INI)
cherrypy.config.update(config)

# prepare locks for each repository
locks = {section: threading.Lock() for section in repos.sections()}

from astrid.pages import BuilderPage, InfoPage, DashboardPage, BuildlogPage

repodir = cherrypy.config.get("repodir")

root = DashboardPage(repodir, repos, locks)
root.build = BuilderPage(repodir, repos, locks)
root.info = InfoPage(repodir, repos, locks)
root.buildlog = BuildlogPage(repodir, repos, locks)

       
