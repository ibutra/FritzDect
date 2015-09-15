import hashlib
from urllib.request import urlopen
from xml.etree.ElementTree import parse


class FritzDect:

    username = 'ibutra'
    password = 'DjWzBhzrsuRf'
    url = "http://192.168.178.1/"
    loginUrl = url + "login_sid.lua?"
    switchUrl = url + "webservices/homeautoswitch.lua?"

    def getSid(self):
        with urlopen(self.loginUrl) as response:
            xml = parse(response)
            sid = xml.findtext('./SID')
            challenge = xml.findtext('./Challenge')

        if sid == '0000000000000000':
            md5 = hashlib.md5()
            md5.update(challenge.encode('utf-16le'))
            md5.update('-'.encode('utf-16le'))
            md5.update(self.password.encode('utf-16le'))
            response = challenge + '-' + md5.hexdigest()
            uri = self.loginUrl + 'username=' + self.username + '&response=' + response
            with urlopen(uri) as response:
                sid = parse(response).findtext('./SID')

            if sid == '0000000000000000':
                raise PermissionError('access denied')

        return sid

    def sendCommand(self, cmd, ain=None):
        uri = self.url + 'webservices/homeautoswitch.lua?sid=' + self.getSid() + "&switchcmd=" + cmd
        if ain is not None:
            uri += '&ain=' + ain
        return urlopen(uri)

    def getDevices(self):
        list = self.getStringResponse('getswitchlist').split(',')
        devices = []
        for ain in list:
            devices.append(FritzDevice(ain, self))
        return devices

    def getStringResponse(self, cmd, ain=None):
        with self.sendCommand(cmd, ain) as f:
            result = f.read()
        return result.decode().strip()

    def getTreeResponse(self, cmd, ain=None):
        with self.sendCommand(cmd, ain) as f:
            result = parse(f)
        return result.getroot()


class FritzDevice:

    def __init__(self, ain, fritzDect):
        self.ain = ain
        self.fritzDect = fritzDect

    def toggle(self):
        return self.fritzDect.getStringResponse('setswitchtoggle', self.ain) == '1'

    def off(self):
        return self.fritzDect.getStringResponse('setswitchoff', self.ain) == '1'

    def on(self):
        return self.fritzDect.getStringResponse('setswitchon', self.ain) == '1'

    def set(self, value):
        if value:
            return self.on()
        else:
            return self.off()

    def getState(self):
        return self.fritzDect.getStringResponse('getswitchstate', self.ain) == '1'

    def getName(self):
        return self.fritzDect.getStringResponse('getswitchname', self.ain)

    def getPower(self):
        mW = float(self.fritzDect.getStringResponse('getswitchpower', self.ain))
        return mW / 1000.0

    def getEnergy(self):
        return int(self.fritzDect.getStringResponse('getswitchenergy', self.ain))

    def getTemperature(self):
        # return self.fritzDect.getStringResponse('gettemperature', self.ain) # unfortunately this currently does not work
        # Workaround:
        xml = self.fritzDect.getTreeResponse('getdevicelistinfos')
        element = xml.find("./device[@identifier='" + self.ain[:5] + " " + self.ain[5:] + "']")
        if element is not None:
            temp = element.find('./temperature/celsius')
            if temp is not None:
                temp = float(temp.text)
                temp = temp / 10.0
                return temp
        return 0.0

if __name__ == "__main__":
    print("Testing...")
    fritz = FritzDect()
    devList = fritz.getDevices()
    for dev in devList:
        print("Name: " + dev.getName())
        print("State: " + str(dev.getState()))
        print("Turning On: " + str(dev.set(True)))
        print("Turning Off: " + str(dev.off()))
        print("Toggle: " + str(dev.toggle()))
        print("Current Power: " + str(dev.getPower()) + "mW")
        print("Used Energy: " + str(dev.getEnergy()) + "Wh")
        print("Temp: " + str(dev.getTemperature()) + 'C')
