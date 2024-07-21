from datetime import datetime
from email.mime.text import MIMEText
import smtplib

class Logger:
    separator = ";"

    def __init__(self, repoName):
        self.repoName = repoName

    def _getLogfile(self):
        return f'/data/log/{self.repoName}.log'

    def _getBuildlogfile(self):
        return f'/data/log/{self.repoName}.build.log'

    def log(self, user, message, sendMail = False):
        logfile = self._getLogfile()
        f = open(logfile, "a")
        f.write(Logger.separator.join([datetime.now().isoformat(' '), message, user]) + "\n")
        f.close()

        if sendMail:
            self._sendMail(message)

    def getLogs(self):
        logfile = self._getLogfile()
        try:
            f = open(logfile, "r")

            records = [row.split(Logger.separator) for row in reversed(list(f))]
            f.close()
            return records
        except:
            return []

    def getBuildLog(self):
        fn = self._getBuildlogfile()
        try:
            f = open(fn, "r")
            res = f.read()
            f.close()
            return res
        except:
            return None

    def _sendMail(self, message):
        headerFrom = cherrypy.config.get("mail_from")
        headerTo = cherrypy.config.get("mail_to")

        msg = MIMEText(message)
        msg['Subject'] = 'Astrid coughed on repo {}'.format(self.repoName)
        msg['From'] = headerFrom
        msg['To'] = headerTo

        try:
            s = smtplib.SMTP('localhost')
            s.sendmail(headerFrom, [headerTo], msg.as_string())
            s.quit()
        except:
            pass
