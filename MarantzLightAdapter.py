import logging
from bridgedata import ExtendedColorLightStateListener, DimmableLightStateListener
from marantz import MarantzIpListener
import re

class PowerMixin():

    #########################################################
    # methods that handle the direction light -> marantz
    #########################################################

    def on_set_power(self, oldValue, newValue):
        self.marantzIp.set_main_zone_power( newValue )
        if newValue:
            self.marantzIp.set_main_zone_input_source(self.input_source)

    #########################################################
    # methods that handle the direction marantz -> light
    #########################################################

    def on_main_zone_power_changed(self, newValue):
        if newValue == False:
            self.light.set_on( False )

    def on_main_zone_input_source_changed(self, newValue):
        self.light.set_on( self.marantzIp.main_zone_powered_on and newValue == self.input_source)


class VolumeMixin():

    def on_set_brightness(self, oldValue, newValue):
        self.marantzIp.set_main_zone_volume( newValue / 255 * int(self.config['Marantz']['maxvolume']) )

    def on_main_zone_volume_changed(self, newValue):
        self.light.set_brightness( int(newValue / int(self.config['Marantz']['maxvolume']) * 255) )


class MarantzFmRadioLightAdapter(PowerMixin, VolumeMixin, ExtendedColorLightStateListener, MarantzIpListener):

    def __init__(self, config, light, marantzIp):
        ExtendedColorLightStateListener.__init__(self)
        light.register_listener(self)
        marantzIp.register_listener(self)
        self.config = config
        self.light = light
        self.marantzIp = marantzIp
        self.input_source = 'TUNER'
        self.logger = logging.getLogger('MarantzFmRadioLightAdapter')
        self.data = []
        self.fileindex = 0



class MarantzMediaPlayerLightAdapter(PowerMixin, VolumeMixin, DimmableLightStateListener, MarantzIpListener):
    def __init__(self, config, light, marantzIp):
        DimmableLightStateListener.__init__(self)
        light.register_listener(self)
        marantzIp.register_listener(self)
        self.config = config
        self.light = light
        self.marantzIp = marantzIp
        self.input_source = 'MPLAY'
        self.logger = logging.getLogger('MarantzMediaPlayerLightAdapter')