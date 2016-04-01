import cherrypy
import FritzDect
import jinja2
import json
from threading import Thread


class FritzServer(object):

    def __init__(self):
        self.fritz = FritzDect.FritzDect()
        self.env = jinja2.Environment(loader=jinja2.PackageLoader("FritzDect","templates"))
        self.update_device_list()
        cherrypy.process.plugins.BackgroundTask(60, self.update_device_list)

    @cherrypy.expose
    def index(self):
        page = self.env.get_template("index.html")
        return page.render(devicelist=self.devicelist)

    @cherrypy.expose
    def switch(self, ain):
        try:
            device = next(dev for dev in self.devicelist if dev.ain == ain)
            thread = Thread(target=device.toggle)   
            thread.start()
        except ValueError:
            pass
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def list(self):
        return json.dumps([{"ain": device.ain, "name": device.getName(), "state": device.getState(), "temp": device.getTemperature()} for device in self.devicelist])

    def update_device_list(self):
        self.devicelist = self.fritz.getDevices()

    @cherrypy.expose
    def status(self, ain):
        device = next(dev for dev in self.devicelist if dev.ain == ain)
        return str(device.getState())


if __name__ == "__main__":
    conf = {
        '/public': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '/Users/stefanrakel/Documents/Projects/FritzDECT/public'
        }
    }
    try:
        config = json.load(open("config"))
        cherrypy.config.update({'server.socket_host': config["server_url"],
                            'server.socket_port': config["server_port"]})
    except json.JSONDecodeError:
        cherrypy.config.update({'server.socket_host': '127.0.0.1',
                            'server.socket_port': 8080})
    cherrypy.quickstart(FritzServer(),config=conf)
