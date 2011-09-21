import SimpleHTTPServer

from BrowsePresenter import BrowsePresenter
from HomePresenter import HomePresenter
from ErrorPresenter import ErrorPresenter
from Template import Template

class Controller(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def getLink(self, presenter, data):
        if presenter == "home":
            return "/"
        elif data == None:
            return "/" + presenter
        else:
            return "/" + presenter + "/" + data
            
    # dispatch
    def getPresenter(self, path):
        print self.path + "\n"
        parts = path.split("/")[1:]
        
        if path == "/":
            print "wants home\n"
            return HomePresenter(self, None)
        elif parts[0] == "build":
            data = "/".join(parts[1:])
            return BuildPresenter(self, data)
        elif parts[0] == "info":
            data = "/".join(parts[1:])
            return InfoPresenter(self, data)
        elif parts[0] == "browse":
            data = "/".join(parts[1:])
            return BrowsePresenter(self, data)
        else:
            return None
        
    def _headers(self):
        presenter = self.getPresenter(self.path)
        if presenter == None or (presenter.getFile() == None and presenter.response() == None):
            self.send_response(404)
            presenter = ErrorPresenter(self, None, 404)
        else:
            self.send_response(200)
        
        pfile = presenter.getFile()
        if pfile != None:
            self.send_header("Content-type", presenter.getContentType())
            self.send_header("Content-length", presenter.getContentLength())            
        else:
            response = presenter.response()
            self.send_header("Content-type", presenter.getContentType())
            self.send_header("Content-length", len(response))
        self.end_headers()
        return presenter
    
    def do_HEAD(self):
        self._headers()
        
    def do_GET(self):
        presenter = self._headers()
        pfile = presenter.getFile()
        if pfile != None:
            self.wfile.writelines(pfile.readline())
        else:
            response = presenter.response()
            self.wfile.write(response)