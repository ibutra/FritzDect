# FritzDect - Python classes for interfacing Fritz!DECT devices
#
# The MIT License (MIT)

# Copyright (c) 2015 Stefan Rakel

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hashlib
from urllib.request import urlopen
from xml.etree.ElementTree import parse
import json


class FritzDect(object):

    def __init__(self):
        config = json.load(open("config"))
        self.username = config["username"]
        self.password = config["password"]
        self.url = config["url"]
        self.loginUrl = self.url + "login_sid.lua?"
        self.switchUrl = self.url + "webservices/homeautoswitch.lua?"

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


class FritzDevice(object):

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
            offset = element.find('./temperature/offset')
            if temp is not None:
                temp = float(temp.text)
                if offset is not None:
                    temp += float(offset.text)
                temp = temp / 10.0
                return temp
        return 0.0

    def getOffset(self):
        xml = self.fritzDect.getTreeResponse('getdevicelistinfos')
        element = xml.find("./device[@identifier='" + self.ain[:5] + " " + self.ain[5:] + "']")
        if element is not None:
            offset = element.find('./temperature/offset')
            if offset is not None:
                offset = float(offset.text) / 10.0
            return offset
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
        print("Temp: " + str(dev.getTemperature()) + '°C')
        print("Temp Offset: " + str(dev.getOffset()) + '°C')
