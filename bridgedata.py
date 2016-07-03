
class BridgeData():

    def __init__(self, config):
        self.lights = {
            "1": {
                "state": {
                    "on": True,
                    "bri": 255,
                    "hue": 0,
                    "sat": 0,
                    "xy": [0.0000, 0.0000],
                    "ct": 0,
                    "alert": "none",
                    "effect": "none",
                    "colormode": "hs",
                    "reachable": True
                },
                "type": "Extended color light",
                "name": "FM Radio",
                "modelid": "LCT001",
                "manufacturername": "Philips",
                "uniqueid": "uniqfmradio",
                "swversion": "65003148",
                "pointsymbol": {}
            },
        }

        self.config = {
            "name": config['HueBridge']['name'],
            "zigbeechannel": 15,
            "bridgeid": config['HueBridge']['bridgeid'],
            "mac": config['HueBridge']['mac'],
            "dhcp": True,
            "ipaddress": config['Server']['host'] + ":" + config['Server']['port'],
            "netmask": config['Server']['netmask'],
            "gateway": config['Server']['gateway'],
            "proxyaddress": "none",
            "proxyport": 0,
            "UTC": "2016-06-30T18:21:35",
            "localtime": "2016-06-30T20:21:35",
            "timezone": "Europe/Berlin",
            "modelid": "BSB002",
            "swversion": "01033370",
            "apiversion": "1.13.0",
            "swupdate": {
                "updatestate": 0,
                "checkforupdate": False,
                "devicetypes": {
                    "bridge": False,
                    "lights": [],
                    "sensors": []
                },
                "url": "",
                "text": "",
                "notify": False
            },
            "linkbutton": False,
            "portalservices": True,
            "portalconnection": "connected",
            "portalstate": {
                "signedon": True,
                "incoming": True,
                "outgoing": True,
                "communication": "disconnected"
            },
            "factorynew": False,
            "replacesbridgeid": None,
            "backup": {
                "status": "idle",
                "errorcode": 0
            },
            "whitelist": {
                config['HueBridge']['user']: {
                    "last use date": "2016-03-11T20:35:57",
                    "create date": "2016-01-28T17:17:16",
                    "name": "MarantzHueAdapter"
                }
            }
        }

        self.data = {
            "lights": self.lights,
            "groups": {},
            "config": self.config,
            "schedules": {}
        }