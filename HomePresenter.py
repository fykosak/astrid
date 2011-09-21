from Presenter import Presenter
from Template import Template
import ConfigParser

class HomePresenter(Presenter):
    def response(self):
        repos = ConfigParser.ConfigParser()
        repos.read("repos.ini")
        
        template = Template("templates/home.html", self)
        
        sections = ""
        for section in repos.sections():
            sections += "<li><a href=\"" + self.controller.getLink("browse", section) + "\">" + section + "</a>" \
            + " (<a href=\"" + self.controller.getLink("info", section) + "\">info</a>)</li>"            
        template.assignData("repos", sections)
        
        template.assignData("pagetitle", "FKS repos")
        return template.render()
