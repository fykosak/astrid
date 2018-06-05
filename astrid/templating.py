import os
import html
import re
import os.path
import pkg_resources

class Template:
    def __init__(self, filename):
        self.filename = filename
        self.includes = {}
        self.data = {}
        
    def assignData(self, name, data):
        self.data[name] = str(data)
        
    def render(self):
        # firstly include files        
        template = pkg_resources.resource_stream('astrid', self.filename).read().decode()
        template = re.sub('\{include ([^\}]*)\}', self._include, template)
        # secondly expand variables
        return re.sub('\{(!)?([^\}]*)\}', self._expand, template)
        
    def _include(self, mo):
        filename = os.path.dirname(self.filename) + "/" + mo.group(1)
        if filename not in self.includes:
            f = pkg_resources.resource_stream('astrid', filename)
            if not f:
                self.includes[filename] = "NOT FOUND"
            else:
                self.includes[filename] = f.read().decode()
                f.close()
        
        return self.includes[filename]
    
    def _expand(self, mo):
        if mo.group(2) in self.data:
            data = self.data[mo.group(2)]
        else:
            data = "undefined"     
        if mo.group(1) == "!":
            return html.escape(data)
        else:
            return data
            
