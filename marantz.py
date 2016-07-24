import threading, telnetlib, re, sys, logging

__author__ = 'Josh'

class MarantzIP():
    sources = ["TUNER", "DVD", "BD", "TV", "SAT", "SAT/CBL", "MPLAY", "GAME", "AUX1", "NET", "PANDORA", "SIRIUSXM",
               "LASTFM", "FLICKR", "FAVORITES", "IRADIO", "SERVER", "USB/IPOD", "USB", "IPD", "IRP", "FVP"]

    def __init__(self, ip):
        self.ip = ip
        self.timer = None  # threading.Timer(10, self.disconnect)
        self.conn = telnetlib.Telnet()
        self.logger = logging.getLogger('server')

    def connect(self):
        try:
            self.logger.debug("Testing existing connection..."),
            self.conn.write("PING\r")
            self.logger.debug("[CONNECTED]")
            self.reset_timer()
        except:
            self.logger.debug("[DISCONNECTED]")
            self.logger.debug("Connecting..."),
            self.conn.open(self.ip, 23, 3)
            self.logger.debug("[CONNECTED]")
            self.start_timer()
        return self.conn

    def disconnect(self):
        self.logger.debug("Disconnecting..."),
        self.conn.close()
        self.logger.debug("[DISCONNECTED]")

    def start_timer(self):
        self.timer = threading.Timer(10, self.disconnect)
        self.timer.start()

    def reset_timer(self):
        self.logger.debug("Resetting timer.")
        self.timer.cancel()
        self.start_timer()

    def dispatch(self, action, *args, **kwargs):
        dispatcher = {"Power": self.set_power, "GetPower": self.get_power,
                      "Mute": self.set_mute, "GetMute": self.get_mute,
                      "Volume": self.set_volume, "GetVolume": self.get_volume,
                      "Input": self.set_source, "GetInput": self.get_source,
                      "Source": self.set_source, "GetSource": self.get_source,
                      "GetStatus": self.get_status
        }
        try:
            return dispatcher[action](*args, **kwargs)
        except KeyError:
            raise ValueError("Invalid key received. '%s' is not valid." % action)

    def query(self, commands, pattern=None):
        response = {}
        t = self.connect()
        # if we got a single item, let's wrap it in a list to satisfy the loop below
        if type(commands) not in [list, tuple]:
            commands = [commands]
        #loop through each command and build+send+parse it
        for command in commands:
            # if a pattern wasn't supplied, let's look for the standard format
            if command.endswith("?\r"):
                action = command[:-2]  # strip ?\r off: \r counts as one return character
            else:
                action = command
                command += "?\r"  # append the query characters ?\r

            if pattern is None:
                pattern = action+"([a-zA-Z0-9]*)\r"
            #send the command to the AVR
            self.logger.debug("Clearing previous buffer...", t.read_very_eager().encode("string_escape"))
            self.logger.debug(("Sending: '%s'" % command).encode('string_escape'))
            self.logger.debug(("Looking for: '%s'" % pattern).encode('string_escape'))
            t.write(command)
            find = t.expect([pattern], 1)
            if find[1] is None:
                self.logger.error("[ERROR] Match failed. Trying one more time...Sending command again.")
                t.write(command)
                find = t.expect([pattern], 1)
            self.logger.debug("Response:", (find[2]).encode("string_escape"))
            matches = find[1]
            response[action] = matches.group(1)
            #reset the pattern for the next run
            pattern = None
            self.reset_timer()
        #t.close()

        return response

    def write_command(self, command):
        t = self.connect()
        t.write(command.encode('ascii'))
        #t.close()
        self.reset_timer()

    def get_status(self, *args):
        return self.query(["PW", "MU", "SI", "MV"])

    def get_source(self, *args):
        return self.query("SI?\r", "SI([^\r]+)\r")
        # 'SIBD\r@SRC:MM\rSVSOURCE\r'

    def set_source(self, source):
        self.write_command("SI" + source + "\r")
        # TODO: extend this to verify if the source changed to what we wanted
        # 'SIDVD\r@SRC:22\rCVFL 49\rCVFR 56\rCVC 52\rCVSW 43\rCVSL 47\rCVSR 455\rCVSBL 50\rCVSBR 50\rCVSB 50\rCVFHL 50\rCVFHR 50\rMVMAX 98\rMSSTEREO\rSDHDMI\r@INP:4\rSVSOURCE\rDCAUTO\r@DCM:3\rPSDCO OFF\rPSDRC AUTO\r'
        # 'SIBD\r@SRC:MM\rCVFL 49\rCVFR 56\rCVC 54\rCVSW 43\rCVSL 47\rCVSR 455\rCVSBL 50\rCVSBR 50\rCVSB 50\rCVFHL 50\rCVFHR 50\rMVMAX 98\rMSDTS NEO:6 M\rSDHDMI\r@INP:4\rSVSOURCE\rDCAUTO\r@DCM:3\rPSDCO OFF\rPSDRC AUTO\rPSLFE 00\rPSBAS 50\r@TOB:000\rPSTRE 50\r@TOT:000\r'

    def get_mute(self, *args):
        return self.query("MU?\r", "MU([^\r]+)\r")
        # 'MUOFF\r@AMT:1\r'

    def set_mute(self, onoff):
        if type(onoff) is not str:
            raise TypeError("Expecting 'ON' or 'OFF'. Received type: " + type(onoff))
        if onoff.upper() not in ["ON", "OFF"]:
            raise ValueError("Expecting 'ON' or 'OFF'. Received " + onoff)
        self.write_command("MU" + onoff.upper() + "\r")
        # 'MUON\r@AMT:2\r'
        # 'MUOFF\r@AMT:1\r'

    def get_power(self, *args):
        return self.query("PW?\r", "PW([^\r]+)\r")
        # 'PWON\r@PWR:2\r'
        # 'PWSTANDBY\r@PWR:1\r'


    def set_power(self, onoff, *args, **kwargs):
        if type(onoff) is not bool:  # and type(onoff) is not unicode
            raise TypeError("Expecting True or False. Received %s of type %s." % (str(onoff), str(type(onoff))))
        if onoff:
            self.write_command("PWON\r")
        else:
            self.write_command("PWSTANDBY\r")
        # 'ZMOFF\r@PWR:1\rPWSTANDBY\r@PWR:1\r'
        # 'ZMON\r@PWR:2\rPWON\r@PWR:2\r'

    def get_volume(self, *args):
        return self.query("MV?\r", "MV([^\r]+)\r")

    def set_volume(self, updown):
        if type(updown) is not int or updown < 0 or updown > 98:
            raise TypeError("Expecting 0 <= updown <= 98. Received type: " + type(updown))
        self.write_command('MV%(vol)02d\r' % {'vol': updown } )
        # MV005\r@VOL:-795\rMVMAX 98\r

import logging
import asyncore
import asynchat
import socket
from io import BytesIO
import math

class AsyncMarantzIpHandler(asynchat.async_chat):

    def __init__(self, address):
        super().__init__()
        self.logger = logging.getLogger('AsyncMarantzIpHandler')
        self.set_terminator( b'\r' )
        self.rfile = BytesIO()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( address )
        self.listeners = []

    def handle_connect(self):
        self.logger.info('Connected!')

    def handle_close(self):
        self.logger.info('Closed!')

    def collect_incoming_data(self, data):
        self.rfile.write( data )

    def found_terminator(self):
        command = self.rfile.getvalue().decode('ascii')
        self.rfile = BytesIO()

        if len(command) < 2:
            self.logger.warn('Invalid command received %s' % command)

        self.logger.debug('received %s with param %s', command[:2], command[2:])
        for listener in self.listeners:
            listener.on_command(command[:2], command[2:])

    def register_listener(self, listener):
        self.listeners.append(listener)

    def set_power(self, onoff):
        if onoff:
            self.push(b"PWON\r")
        else:
            self.push(b"PWSTANDBY\r")

    def push_str(self, str):
        self.push(str.encode('ascii'))

    def set_volume(self, value):
        frac, whole = math.modf(value)
        if frac < 0.25:
            self.push_str('MV%02d\r' % (whole))
        elif frac > 0.75:
            self.push_str('MV%02d\r' % (whole + 1) )
        else:
            self.push_str('MV%02d5\r' % (whole) )

class MarantzIpListener():
    def on_command(self, command, parameter):
        pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s' )
    logger = logging.getLogger('main')

    class SillyHandler(MarantzIpListener):
        def on_command(self, command, parameter):
            logger.info('received %s with param %s' % (command, parameter))

    handler = AsyncMarantzIpHandler( ('192.168.12.4', 23) )
    handler.register_listener(SillyHandler())
    try:
        asyncore.loop()
    except:
        logger.info('stopping')
        handler.close()