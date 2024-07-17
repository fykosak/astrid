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
        return f'/data/log/{reponame}.log'

    def _getBuildlogfile(self, reponame):
        return f'/data/log/{reponame}.build.log'

    def log(self, reponame, user, message, sendMail = False):
        logfile = self._getLogfile(reponame)
        f = open(logfile, "a")
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
        msg['Subject'] = 'Astrid coughed on repo {}'.format(reponame)
        msg['From'] = headerFrom
        msg['To'] = headerTo

        try:
            s = smtplib.SMTP('localhost')
            s.sendmail(headerFrom, [headerTo], msg.as_string())
            s.quit()
        except:
            pass


from configparser import ConfigParser

REPOS_INI = '/data/config/repos.ini'
CONFIG_INI = '/data/config/config.ini'

repos = ConfigParser()
repos.read(os.path.expanduser(REPOS_INI))
cherrypy.engine.autoreload.files.add(REPOS_INI)

config = os.path.expanduser(CONFIG_INI)
cherrypy.config.update(config)

# prepare locks for each repository
locks = {section: threading.Lock() for section in repos.sections()}
waitLocks = {section: threading.Lock() for section in repos.sections()}

from astrid.pages import BuilderPage, InfoPage, DashboardPage, BuildlogPage

repodir = cherrypy.config.get("repodir")

root = DashboardPage(repodir, repos, locks, waitLocks)
root.build = BuilderPage(repodir, repos, locks, waitLocks)
root.info = InfoPage(repodir, repos, locks, waitLocks)
root.buildlog = BuildlogPage(repodir, repos, locks, waitLocks)
