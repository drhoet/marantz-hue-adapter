import logging
from bridgedata import ExtendedColorLightStateListener, DimmableLightStateListener
from marantz import MarantzIpListener
import re
from colorspaces import gamut_c
import math

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

    def dist(self, x1, x2):
        return math.sqrt((x1[0] - x2[0])**2 + (x1[1] - x2[1])**2)

    def on_set_colorxy(self, oldValue, newValue):
        index, xy = min(enumerate(gamut_c), key=lambda x: self.dist(newValue, x[1]))
        self.marantzIp.set_tuner_freq(index / 20.0 + 87.50)

    def on_tuner_freq_changed(self, newValue):
        xy = gamut_c[(int)((newValue-87.50)*20)]
        self.light.set_xy(xy)


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