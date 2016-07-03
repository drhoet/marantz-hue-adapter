#!flask/bin/python
from flask import Flask, jsonify, request
from config import Configurator
from bridgedata import BridgeData
from marantz import MarantzIP

import logging

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to the Marantz Hue adapter. Control you marantz receiver as if it were a Hue Light!"

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
        marantzIp.set_power( newValue )
    elif param == 'bri':
        marantzIp.set_volume( int(newValue / 255 * int(config['Marantz']['maxvolume'])) )

if __name__ == '__main__':
    # init logging
    logging.config.fileConfig('log.cfg')
    logger = logging.getLogger('server')

    logger.info('Starting marantz-hue-adapter server')
    config = Configurator().config

    marantzIp = MarantzIP( config['Marantz']['host'] )
    bridgeData = BridgeData( config )
    app.run(host=config['Server']['host'], port=int(config['Server']['port']), debug=True)