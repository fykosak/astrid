import cherrypy

class BasePage(object):
    def __init__(self, repodir, repos):
        self.repos = repos
        self.repodir = repodir
    
    def _checkAccess(self, reponame):
        user = cherrypy.request.login
        if user not in self.repos.get(reponame, "users"):
            raise cherrypy.HTTPError(401)
        
