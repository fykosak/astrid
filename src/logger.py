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
    
    @staticmethod
    def _format_time_ago(time_str):
        try:
            time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
            now = datetime.now()
            diff = now - time

            if diff.days > 0:
                if diff.days == 1:
                    return "1 day ago"
                return f"{diff.days} days ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                if hours == 1:
                    return "1 hour ago"
                return f"{hours} hours ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                if minutes == 1:
                    return "1 minute ago"
                return f"{minutes} minutes ago"
            else:
                return "just now"
        except ValueError:
            return time_str # orig if parse fails


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
        
    def get_current_build_status(self):
        logfile = self._getLogfile()
        try:
            with open(logfile, "r") as f:
                record_lines = f.readlines()
            if len(record_lines) != 0:  
                last_record = record_lines[-1].strip().split(Logger.separator)
                
                return {
                    "status": "succeeded" if "Build succeeded." in last_record[1] else "failed" if "Build failed." in last_record[1] else "unknown",
                    "timeinfo": self._format_time_ago(last_record[0]),
                    "user": last_record[2]
                }
        except:
            pass
        return {"status": "unknown", "timeinfo": "-", "user": "-"}

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
