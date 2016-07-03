import os, logging, logging.config, configparser

class Configurator():

    def __init__(self):
        self.logger = logging.getLogger('config')
            # loading configuration
        self.logger.debug('Loading config')
        if not os.path.isfile('server.cfg'):
            writeDefaultConfig()
            quit()

        self.config = configparser.ConfigParser()
        self.config.read('server.cfg')

    def writeDefaultConfig():
        self.logger.debug('No config found. Writing default config to server.cfg. Please adapt accordingly and restart the server.')
        config = configparser.ConfigParser()
        config['Server'] = {
            'host': '192.168.0.x',
            'port': '8080',
            'gateway': '192.168.0.1',
            'netmask': '255.255.255.0',
        }
        config['HueBridge'] = {
            'mac': 'xx:xx:xx:xx:xx:xx',
            'name': 'Marantz Hue',
            'bridgeid': 'brigdeId',
            'user': 'MarantzHueUser',
        }
        config['Marantz'] = {
            'ip': '192.168.0.x',
            'maxvolume': '50'
        }
        with open('server.cfg', 'w') as configfile:
            config.write(configfile)
