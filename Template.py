import os # template
import cgi # template
import re # template
import os.path

class Template:
    def __init__(self, filename):
        self.filename = os.path.join(os.path.dirname(__file__), filename)
        self.includes = {}
        self.data = {}
        
    def assignData(self, name, data):
        self.data[name] = str(data)
        
    def render(self):
        # firstly include files        
        template = open(self.filename).read()
        template = re.sub('\{include ([^\}]*)\}', self._include, template)
        # secondly expand variables
        return re.sub('\{(!)?([^\}]*)\}', self._expand, template)
        
    def _include(self, mo):
        filename = os.path.dirname(self.filename) + "/" + mo.group(1)
        if filename not in self.includes:
            if not os.path.exists(filename):
                self.includes[filename] = "NOT FOUND"
            else:
                f = open(filename)
                self.includes[filename] = f.read()
                f.close()
        
        return self.includes[filename]
    
    def _expand(self, mo):
        if mo.group(2) in self.data:
            data = self.data[mo.group(2)]
        else:
            data = "undefined"     
        if mo.group(1) == "!":
            return cgi.escape(data)
        else:
            return data
            
