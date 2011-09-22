import cherrypy
import os.path
import cherrypy.lib.auth_basic

import htmldir
import staticdirindex

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
        for section in self.repos.sections():
            repos += """<li><a href="%s">%s</a> (<a href="info/%s">info</a>)</li>""" % (section, section, section,)
        template.assignData("pagetitle", "FKS repos")
        template.assignData("repos", repos)
        return template.render()
        

    index._cp_config = {'tools.staticdir.on': False}



repos = ConfigParser()
repos.read(repofile)

root = Server(repos)
root.build = BuilderPage(os.path.join(rootdir, cherrypy.config.get("repodir")), repos)
root.info = InfoPage(os.path.join(rootdir, cherrypy.config.get("repodir")), repos)


#cherrypy.quickstart(root, config=conffile)
