import logging
from bridgedata import ExtendedColorLightStateListener
from marantz import MarantzIpListener
import re

class MarantzLightAdapter(ExtendedColorLightStateListener, MarantzIpListener):

    def __init__(self, config, light, marantzIp):
        ExtendedColorLightStateListener.__init__(self)
        light.register_listener(self)
        marantzIp.register_listener(self)
        self.config = config
        self.light = light
        self.marantzIp = marantzIp
        self.logger = logging.getLogger('MarantzLightAdapter')

    #########################################################
    # methods that handle the direction light -> marantz
    #########################################################
    def on_power_changed(self, oldValue, newValue):
        self.marantzIp.set_power( newValue )

    def on_brightness_changed(self, oldValue, newValue):
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

    def on_command_zm(self, parameter):
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