import ConfigParser
import os

from Presenter import Presenter
from Template import Template

class BrowsePresenter(Presenter):
    datadir = "data"
    _response = None
    _ctype = None
    _clen = None
    
    def getFile(self):
        repos = ConfigParser.ConfigParser()
        repos.read("repos.ini")
        
        parts = [part for part in self.data.split("/") if part != ""]
        if parts[0] not in repos.sections():
            return None
            
        self.data = "/".join(parts)
        path = self.datadir + "/" + "/".join(parts)
        
        if os.path.isdir(path):
            template = Template("templates/dir.html", self)
            if len(parts) > 1:
                files = "<li><a href=\"" + self.controller.getLink("browse", "/".join(parts[:-1])) + "\">..</a></li>"
            else:
                files = ""
            tmp = os.listdir(path)
            tmp.sort()
            for entry in tmp:
                if os.path.isdir(path + "/" + entry):
                    entry += "/"
                files += "<li><a href=\"" + self.controller.getLink("browse", self.data + "/" + entry) + "\">" + entry + "</a></li>"
            template.assignData("files", files)
            template.assignData("dirname", path)
            template.assignData("pagetitle", path)
            self._response = template.render()
        elif os.path.isfile(path):            
            extension = os.path.splitext(path)[1][1:]
            if extension in ["sty", "tex", "mp", "html", "txt", "plt", "csv"]:
                template = Template("templates/textfile.html", self)
                f = open(path)
                template.assignData("pagetitle", path)
                template.assignData("filename", path)
                template.assignData("extension", extension)
                template.assignData("filecontent", f.read())
                f.close()
                self._response = template.render()
            else:
                self._clen = os.path.getsize(path)
                if extension in self.controller.extensions_map:
                    self._ctype = self.controller.extensions_map[extension]
                else:
                    self._ctype = self.controller.extensions_map[""]
                return open(path)
        
        return None
            
    def response(self):
        return self._response
        
    def getContentType(self):
        return self._ctype
    
    def getContentLength(self):
        return self._clen
        
