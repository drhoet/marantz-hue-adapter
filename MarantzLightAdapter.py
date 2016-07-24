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
    def on_set_power(self, oldValue, newValue):
        self.marantzIp.set_main_zone_power( newValue )

    def on_set_brightness(self, oldValue, newValue):
        self.marantzIp.set_main_zone_volume( newValue / 255 * int(self.config['Marantz']['maxvolume']) )

    #########################################################
    # methods that handle the direction marantz -> light
    #########################################################
    def on_main_zone_power_changed(self, newValue):
        self.light.set_on( newValue )

    def on_main_zone_volume_changed(self, newValue):
        self.light.set_brightness( int(newValue / int(self.config['Marantz']['maxvolume']) * 255) )