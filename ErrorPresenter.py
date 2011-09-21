from Presenter import Presenter
from Template import Template

class ErrorPresenter(Presenter):
    def __init__(self, controller, data, code):
        Presenter.__init__(self, controller, data)
        self.code = code
    def response(self):
        template = Template("templates/error.html", self)
        template.assignData("pagetitle", str(self.code) + " " + self.controller.responses[self.code][1])
        template.assignData("code", self.code)
        template.assignData("message", self.controller.responses[self.code][1])
        return template.render()
