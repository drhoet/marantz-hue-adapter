import json
import logging

# Remark: this class is not thread-safe. It doesn't have to be, since everything is running on 1 thread: the server
# is an async server...

class BridgeData():

    def __init__(self, config):
        self.lights = {}

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

class Light():

    def __init__(self, name, uniqueid, manufacturername='drhoet', swversion='0'):
        self.type = ''
        self.name = name
        self.modelid = ''
        self.manufacturername = manufacturername
        self.uniqueid = uniqueid
        self.swversion = swversion
        self.state = {}
        self.listeners = []

    def set_state_property(self, property_name, property_value):
        oldValue = self.state[property_name]
        for listener in self.listeners:
            listener.on_set_state_property(property_name, oldValue, property_value)
        self.internal_set_state_property(property_name, property_value)

    def internal_set_state_property(self, property_name, property_value):
        self.state[property_name] = property_value

    def internal_set_bool(self, property_name, property_value):
        if property_value:
            self.internal_set_state_property(property_name, True)
        else:
            self.internal_set_state_property(property_name, False)

    def internal_set_int(self, property_name, property_value, minValue, maxValue):
        if property_value > maxValue:
            self.internal_set_state_property(property_name, maxValue)
        elif property_value < minValue:
            self.internal_set_state_property(property_name, minValue)
        else:
            self.internal_set_state_property(property_name, property_value)

    def register_listener(self, listener):
        self.listeners.append(listener)

    def asJsonable(self):
        return { 'type': self.type, 'name': self.name, 'modelid': self.modelid, 'manufacturername': self.manufacturername,
            'uniqueid': self.uniqueid, 'swversion': self.swversion, 'state': self.state }

class LightStateListener():

    def __init__(self):
        self.prop_func_map = {}
        self.logger = logging.getLogger('LightStateListener')

    def on_set_state_property(self, name, oldValue, newValue):
        self.logger.debug('Setting %s to: %s', name, newValue)
        if name in self.prop_func_map:
            self.prop_func_map[name](oldValue, newValue)
        else:
            self.logger.warn('Property not supported: %s', name)


class DimmableLight(Light):

    def __init__(self, name, uniqueid):
        super().__init__(name, uniqueid)
        self.type = 'Dimmable light'
        self.modelid = 'LWB006'
        self.state = {
            "on": True,
            "bri": 255,
            "alert": "none",
            "reachable": True
        }

    def set_on(self, value):
        self.internal_set_bool('on', value)

    def set_brightness(self, value):
        self.internal_set_int('bri', value, 0, 255)

    def set_reachable(self, value):
        self.internal_set_bool('reachable', value)

class DimmableLightStateListener(LightStateListener):

    def __init__(self):
        super().__init__()
        self.prop_func_map['on'] = self.on_set_power
        self.prop_func_map['bri'] = self.on_set_brightness
        self.prop_func_map['alert'] = self.on_set_alert
        self.prop_func_map['reachable'] = self.on_set_reachable

    def on_set_power(self, oldValue, newValue):
        pass
    def on_set_brightness(self, oldValue, newValue):
        pass
    def on_set_alert(self, oldValue, newValue):
        pass
    def on_set_reachable(self, oldValue, newValue):
        pass

class ExtendedColorLight(DimmableLight):

    def __init__(self, name, uniqueid):
        super().__init__(name, uniqueid)
        self.type = 'Extended color light'
        self.modelid = 'LLC020' #taking a HueGo: color gamut C is richer than gamut B
        self.state = {
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
        }

    def set_xy(self, value):
        self.internal_set_state_property('xy', value)

class ExtendedColorLightStateListener(DimmableLightStateListener):

    def __init__(self):
        super().__init__()
        self.prop_func_map['hue'] = self.on_set_hue
        self.prop_func_map['sat'] = self.on_set_saturation
        self.prop_func_map['xy'] = self.on_set_colorxy
        self.prop_func_map['ct'] = self.on_set_colorct
        self.prop_func_map['effect'] = self.on_set_effect
        self.prop_func_map['colormode'] = self.on_set_colormode

    def on_set_hue(self, oldValue, newValue):
        pass
    def on_set_saturation(self, oldValue, newValue):
        pass
    def on_set_colorxy(self, oldValue, newValue):
        pass
    def on_set_colorct(self, oldValue, newValue):
        pass
    def on_set_effect(self, oldValue, newValue):
        pass
    def on_set_colormode(self, oldValue, newValue):
        pass

class BridgeDataJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Light):
            return obj.asJsonable()
        # Let the base class default method raise the TypeError
        return super().default(obj)