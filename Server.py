import cherrypy
import os.path
import htmldir
import staticdirindex
from Template import Template
from ConfigParser import ConfigParser
from BuilderPage import BuilderPage
from InfoPage import InfoPage

conffile = os.path.join(os.path.dirname(__file__), 'config.ini')
cherrypy.config.update(conffile)
rootdir = os.path.dirname(os.path.abspath(__file__))


class StaticAndDynamic(object):
    _cp_config = {'tools.staticdir.on' : True,
                  'tools.staticdir.dir' : os.path.join(rootdir, cherrypy.config.get("repodir")),
                  'tools.staticdir.indexlister': htmldir.htmldir,
#                  'tools.staticdir.index' : 'index.html',
    }
    
    def __init__(self):
        self.repos = ConfigParser()
        self.repos.read('repos.ini')


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






root = StaticAndDynamic()
root.build = BuilderPage(os.path.join(rootdir, cherrypy.config.get("repodir")))
root.info = InfoPage(os.path.join(rootdir, cherrypy.config.get("repodir")))

cherrypy.quickstart(root, config=conffile)