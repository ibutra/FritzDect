import cherrypy
import FritzDect
import jinja2


class FritzServer(object):

    def __init__(self):
        self.fritz = FritzDect.FritzDect()
        self.env = jinja2.Environment(loader=jinja2.PackageLoader("FritzDect","templates"))

    @cherrypy.expose
    def index(self):
        devicelist = self.fritz.getDevices()
        page = self.env.get_template("index.html")
        return page.render(devicelist=devicelist)

    @cherrypy.expose
    def switch(self, ain):
        deviceList = self.fritz.getDevices()
        device = None
        for dev in deviceList:
            if dev.ain == ain:
                device = dev
                break
        if device is not None:
            device.toggle()
        return self.index()



cherrypy.quickstart(FritzServer())
