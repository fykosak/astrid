import cherrypy
import os.path
import cherrypy.lib.auth_basic

import htmldir

from Template import Template
from ConfigParser import ConfigParser
from BuilderPage import BuilderPage
from InfoPage import InfoPage

conffile = os.path.join(os.path.dirname(__file__), 'config.ini')
repofile = os.path.join(os.path.dirname(__file__), 'repos.ini')
cherrypy.config.update(conffile)
rootdir = os.path.dirname(os.path.abspath(__file__))


class Server(object):
    _cp_config = {'tools.staticdir.on' : True,
                  'tools.staticdir.dir' : os.path.join(rootdir, cherrypy.config.get("repodir")),
                  'tools.staticdir.indexlister': htmldir.htmldir,
#                  'tools.staticdir.index' : 'index.html',
    }
    
    def __init__(self, repos):
        self.repos = repos


    @cherrypy.expose
    def index(self, **params):
        template = Template('templates/home.html')
        repos = ""
        user = cherrypy.request.login
        for section in self.repos.sections():
            if user in self.repos.get(section, "users").split(","):
                repos += """<li><a href="%s">%s</a> (<a href="info/%s">info</a>)</li>""" % (section, section, section,)
                
        template.assignData("pagetitle", "FKS repos")
        template.assignData("repos", repos)
        template.assignData("user", user)
        return template.render()
        

    index._cp_config = {'tools.staticdir.on': False}



repos = ConfigParser()
repos.read(repofile)

import staticdirindex
staticdirindex.repos = repos

root = Server(repos)
root.build = BuilderPage(os.path.join(rootdir, cherrypy.config.get("repodir")), repos)
root.info = InfoPage(os.path.join(rootdir, cherrypy.config.get("repodir")), repos)


#cherrypy.quickstart(root, config=conffile)
