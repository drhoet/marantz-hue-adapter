import logging
from bridgedata import LightStateListener
from marantz import MarantzIpListener
import re

class MarantzLightAdapter(LightStateListener, MarantzIpListener):

    def __init__(self, config, light, marantzIp):
        light.register_listener(self)
        marantzIp.register_listener(self)
        self.config = config
        self.light = light
        self.marantzIp = marantzIp
        self.logger = logging.getLogger('MarantzLightAdapter')

    #########################################################
    # methods that handle the direction light -> marantz
    #########################################################
    def on_set_state_property(self, name, oldValue, newValue):
        mname = 'on_set_' + name.lower()
        if hasattr(self, mname):
            getattr(self, mname)(oldValue, newValue)
        self.logger.warn('Ignoring state update: %s with value %s', name, newValue)

    def set_state_property(self, property_name, property_value):
        super().set_state_property(property_name, property_value)

    def on_set_on(self, oldValue, newValue):
        self.marantzIp.set_power( newValue )

    def on_set_bri(self, oldValue, newValue):
        self.marantzIp.set_volume( newValue / 255 * int(self.config['Marantz']['maxvolume']) )

    #########################################################
    # methods that handle the direction marantz -> light
    #########################################################
    def on_command(self, command, parameter):
        mname = 'on_command_' + command.lower()
        if hasattr(self, mname):
            getattr(self, mname)(parameter)
        else:
            self.logger.warn('Ignoring command: %s with value %s', command, parameter)

    def on_command_pw(self, parameter):
        self.light.set_on(parameter == 'ON')

    def on_command_mv(self, parameter):
        if re.match('\d\d\d', parameter):
            newValue = float(parameter) / 10
        elif re.match('\d\d', parameter):
            newValue = float(parameter)
        else:
            self.logger.debug('Ignoring invalid volume value %s', parameter)
            return
        
        self.logger.debug('Setting brightness to: %s', newValue)
        self.light.set_brightness( int(newValue / int(self.config['Marantz']['maxvolume']) * 255) )