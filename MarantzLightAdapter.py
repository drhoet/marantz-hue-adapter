import logging
from bridgedata import ExtendedColorLightStateListener, DimmableLightStateListener
from marantz import MarantzIpListener
import re

class MarantzFmRadioLightAdapter(ExtendedColorLightStateListener, MarantzIpListener):

    def __init__(self, config, light, marantzIp):
        ExtendedColorLightStateListener.__init__(self)
        light.register_listener(self)
        marantzIp.register_listener(self)
        self.config = config
        self.light = light
        self.marantzIp = marantzIp
        self.logger = logging.getLogger('MarantzFmRadioLightAdapter')

    #########################################################
    # methods that handle the direction light -> marantz
    #########################################################
    def on_set_power(self, oldValue, newValue):
        self.marantzIp.set_main_zone_power( newValue )
        if newValue:
            self.marantzIp.set_main_zone_input_source('IRP')

    def on_set_brightness(self, oldValue, newValue):
        self.marantzIp.set_main_zone_volume( newValue / 255 * int(self.config['Marantz']['maxvolume']) )

    #########################################################
    # methods that handle the direction marantz -> light
    #########################################################
    def on_main_zone_power_changed(self, newValue):
        if newValue == False:
            self.light.set_on( False )

    def on_main_zone_volume_changed(self, newValue):
        self.light.set_brightness( int(newValue / int(self.config['Marantz']['maxvolume']) * 255) )

    def on_main_zone_input_source_changed(self, newValue):
        self.light.set_on( self.marantzIp.main_zone_powered_on and (newValue == 'IRADIO' or newValue == 'IRP') )


class MarantzMediaPlayerLightAdapter(DimmableLightStateListener, MarantzIpListener):
    def __init__(self, config, light, marantzIp):
        DimmableLightStateListener.__init__(self)
        light.register_listener(self)
        marantzIp.register_listener(self)
        self.config = config
        self.light = light
        self.marantzIp = marantzIp
        self.logger = logging.getLogger('MarantzMediaPlayerLightAdapter')

    #########################################################
    # methods that handle the direction light -> marantz
    #########################################################
    def on_main_zone_power_changed(self, newValue):
        if newValue == False:
            self.light.set_on( False )

    def on_set_power(self, oldValue, newValue):
        self.marantzIp.set_main_zone_power( newValue )
        if newValue:
            self.marantzIp.set_main_zone_input_source('MPLAY')

    def on_set_brightness(self, oldValue, newValue):
        self.marantzIp.set_main_zone_volume( newValue / 255 * int(self.config['Marantz']['maxvolume']) )

    #########################################################
    # methods that handle the direction marantz -> light
    #########################################################
    def on_main_zone_volume_changed(self, newValue):
        self.light.set_brightness( int(newValue / int(self.config['Marantz']['maxvolume']) * 255) )

    def on_main_zone_input_source_changed(self, newValue):
        self.light.set_on( self.marantzIp.main_zone_powered_on and newValue == 'MPLAY' )
