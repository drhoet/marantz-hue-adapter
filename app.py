#!flask/bin/python
from flask import Flask, jsonify, request, make_response
from functools import wraps
from uuid import getnode as get_mac
from marantz import MarantzIP
import os, logging, logging.config, configparser
from bridgedata import BridgeData

app = Flask(__name__)

def init_globals():
    global marantz, bridgeData

    marantz = MarantzIP(config['Marantz']['host'])
    bridgeData = BridgeData(config)

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/api/config', methods=['GET'])
def api_config():
    return jsonify( bridgeData.config )

@app.route('/api/', methods=['POST'])
def create_user():
    return jsonify( [ { "success": { "username": config['HueBridge']['user'] } } ] )

@app.route('/api/<string:username>', methods=['GET'])
def api_username(username):
    if(username == "null"):
        return jsonify( [ { "error": { "type": 1, "address": "/", "description": "unauthorized user" } } ] )
    else:
        return jsonify( bridgeData.data )

@app.route('/api/<string:username>/lights/<string:id>/name', methods=['PUT'])
def lightsPutName(username, id):
    jsonData = request.get_json(force=True)
    bridgeData.lights[id]["name"] = jsonData["name"]
    return ""

@app.route('/api/<string:username>/lights/<string:id>/state', methods=['PUT'])
def lightsPutState(username, id):
    jsonData = request.get_json(force=True)
    logger.debug(jsonData)
    for key, newValue in jsonData.items():
        oldValue = bridgeData.lights[id]["state"][key]
        if oldValue != newValue:
            handleLightStateUpdate(key, oldValue, newValue)
            bridgeData.lights[id]["state"][key] = jsonData[key]

    return ""

def handleLightStateUpdate(param, oldValue, newValue):
    logger.debug('handle update of %s from %s to %s', param, oldValue, newValue)

    if param == 'on':
        marantz.set_power(newValue)
    elif param == 'bri':
        marantz.set_volume( int(newValue / 255 * int(config['Marantz']['maxvolume'])) )

def writeDefaultConfig():
    logger.debug('No config found. Writing default config to server.cfg. Please adapt accordingly and restart the server.')
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

if __name__ == '__main__':
    # init logging
    logging.config.fileConfig('log.cfg')
    logger = logging.getLogger('server')

    logger.info('Starting marantz-hue-adapter server')
    # loading configuration
    logger.debug('Loading config')
    if not os.path.isfile('server.cfg'):
        writeDefaultConfig()
        quit()

    config = configparser.ConfigParser()
    config.read('server.cfg')

    init_globals()

    app.run(host=config['Server']['host'], port=int(config['Server']['port']), debug=True)