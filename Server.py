import cherrypy
import FritzDect
import jinja2
from cherrypy.process.plugins import Daemonizer


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
        raise cherrypy.HTTPRedirect('/')


if __name__ == "__main__":
    d = Daemonizer(cherrypy.engine)
    d.subscribe()
    conf = {
        '/public': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    cherrypy.config.update({'server.socket_host': '192.168.178.38',
                            'server.socket_port': '80'})
    cherrypy.quickstart(FritzServer())
