class Presenter:
    def __init__(self, controller, data):
        self.controller = controller
        self.data = data
    
    def getFile(self):
        return None
    def getContentType(self):
        pass
    def getContentLength(self):
        pass
    
    def response(self):
        return None
