from datetime import datetime
import cherrypy
import os.path

class BuildLogger:
    separator = ";"
    
    def __init__(self, repodir):
        self.repodir = repodir
        
    def _getLogfile(self, reponame):
        return os.path.join(self.repodir, reponame, ".log")
        
    def log(self, reponame, message):
        logfile = self._getLogfile(reponame)
        f = open(logfile, "a")
        user = cherrypy.request.login
        f.write(BuildLogger.separator.join([str(datetime.now()), message, user]) + "\n")
        f.close()
    
    def getLogs(self, reponame):
        logfile = self._getLogfile(reponame)
        try:
            f = open(logfile, "r")
                
            records = [row.split(BuildLogger.separator) for row in reversed(list(f))]
            f.close()
            return records
        except:
            return []
        