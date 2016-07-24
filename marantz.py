import logging
import math
import re
from AsyncSocketHandler import AsyncSocketHandler

class MarantzIp(AsyncSocketHandler):

    def __init__(self, address):
        super().__init__(address)
        self.listeners = []
        self.logger = logging.getLogger('AsyncMarantzIpHandler')
        self.prop_func_map = {
            'ZM': self.handle_command_main_zone_power,
            'MV': self.handle_command_main_zone_volume,
            'SI': self.handle_command_main_zone_input_source_changed,
        }
        self.main_zone_powered_on = False

    def write_command(self, str):
        self.push(str.encode('ascii') + b'\r')

    def command_received(self, command):
        if len(command) < 2:
            self.logger.warn('Invalid command received %s' % command)

        command_key = command[:2]
        command_param = command[2:]
        self.logger.debug('Received %s with param %s', command_key, command_param)


        if command_key in self.prop_func_map:
            self.prop_func_map[command_key](command_param)
        else:
            self.logger.warn('Command not supported: %s', command_key)

    def register_listener(self, listener):
        self.listeners.append(listener)

    def set_main_zone_power(self, onoff):
        if onoff:
            self.write_command('ZMON')
        else:
            self.write_command('ZMOFF')

    def handle_command_main_zone_power(self, parameter):
        self.main_zone_powered_on = parameter == 'ON'
        for listener in self.listeners:
            listener.on_main_zone_power_changed( parameter == 'ON' )
        self.write_command('SI?')

    def set_main_zone_volume(self, value):
        frac, whole = math.modf(value)
        if frac < 0.25:
            self.write_command('MV%02d' % (whole))
        elif frac > 0.75:
            self.write_command('MV%02d' % (whole + 1) )
        else:
            self.write_command('MV%02d5' % (whole) )

    def handle_command_main_zone_volume(self, parameter):
        if re.match('\d\d\d', parameter):
            newValue = float(parameter) / 10
        elif re.match('\d\d', parameter):
            newValue = float(parameter)
        else:
            self.logger.debug('Ignoring invalid volume value %s', parameter)
            return
        
        self.logger.debug('Setting brightness to: %s', newValue)
        for listener in self.listeners:
            listener.on_main_zone_volume_changed( newValue )

    def set_main_zone_input_source(self, value):
        self.write_command('SI' + value)

    def handle_command_main_zone_input_source_changed(self, parameter):
        for listener in self.listeners:
            listener.on_main_zone_input_source_changed( parameter )


class MarantzIpListener():
    def on_main_zone_power_changed(self, newValue):
        pass
    def on_main_zone_volume_changed(self, newValue):
        pass
    def on_main_zone_input_source_changed(self, newValue):
        pass