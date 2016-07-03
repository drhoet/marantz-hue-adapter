#!flask/bin/python
from flask import Flask, jsonify, request, make_response
from functools import wraps
from uuid import getnode as get_mac
from marantz import MarantzIP
import os, logging, logging.config, configparser

app = Flask(__name__)

def init_globals():
  global marantz, bridge_config, lights, api_username_response

  marantz = MarantzIP(config['Marantz']['host'])

  bridge_config = {
  	"name": config['HueBridge']['name'], 
  	"swversion": "01033370",
  	"apiversion": "1.13.0",
  	"mac": config['HueBridge']['mac'],
  	"bridgeid": config['HueBridge']['bridgeid'],
  	"factorynew": False,
  	"replacesbridgeid": None,
  	"modelid": "BSB002"
  }

  lights = {
    "1": {
        "state": {
            "on": True,
            "bri": 255,
            "hue": 0,
            "sat": 0,
            "xy": [0.0000, 0.0000],
            "ct": 0,
            "alert": "none",
            "effect": "none",
            "colormode": "hs",
            "reachable": True
        },
        "type": "Extended color light",
        "name": "FM Radio",
        "modelid": "LCT001",
        "manufacturername": "Philips",
        "uniqueid": "uniqfmradio",
        "swversion": "65003148",
        "pointsymbol": {
            "1": "none",
            "2": "none",
            "3": "none",
            "4": "none",
            "5": "none",
            "6": "none",
            "7": "none",
            "8": "none"
        }
    },
  }

  api_username_response = {
      "lights": lights,
      "groups": {
          "1": {
              "action": {
                  "on": True,
                  "bri": 254,
                  "hue": 33536,
                  "sat": 144,
                  "xy": [0.3460, 0.3568],
                  "ct": 201,
                  "effect": "none",
                  "colormode": "xy"
              },
              "lights": ["1"],
              "name": "Group 1"
          }
      },
      "config": {
          "name": bridge_config["name"],
          "zigbeechannel": 15,
          "bridgeid": bridge_config["bridgeid"],
          "mac": bridge_config["mac"],
          "dhcp": True,
          "ipaddress": config['Server']['host'] + ":" + config['Server']['port'],
          "netmask": config['Server']['netmask'],
          "gateway": config['Server']['gateway'],
          "proxyaddress": "none",
          "proxyport": 0,
          "UTC": "2016-06-30T18:21:35",
          "localtime": "2016-06-30T20:21:35",
          "timezone": "Europe/Berlin",
          "modelid": bridge_config["modelid"],
          "swversion": bridge_config["swversion"],
          "apiversion": bridge_config["apiversion"],
          "swupdate": {
              "updatestate": 0,
              "checkforupdate": False,
              "devicetypes": {
                  "bridge": False,
                  "lights": [],
                  "sensors": []
              },
              "url": "",
              "text": "",
              "notify": False
          },
          "linkbutton": False,
          "portalservices": True,
          "portalconnection": "connected",
          "portalstate": {
              "signedon": True,
              "incoming": True,
              "outgoing": True,
              "communication": "disconnected"
          },
          "factorynew": bridge_config["factorynew"],
          "replacesbridgeid": bridge_config["replacesbridgeid"],
          "backup": {
              "status": "idle",
              "errorcode": 0
          },
          "whitelist": {
              config['HueBridge']['user']: {
                "last use date": "2016-03-11T20:35:57",
                "create date": "2016-01-28T17:17:16",
                "name": "MarantzHueAdapter"
              }
          }
      },
      "schedules": {}
  }

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/api/config', methods=['GET'])
def api_config():
    return jsonify( bridge_config )

@app.route('/api/', methods=['POST'])
def create_user():
	return jsonify( [ { "success": { "username": config['HueBridge']['user'] } } ] )

@app.route('/api/<string:username>', methods=['GET'])
def api_username(username):
	if(username == "null"):
		return jsonify( [ { "error": { "type": 1, "address": "/", "description": "unauthorized user" } } ] )
	else:
		return jsonify( api_username_response )

@app.route('/api/<string:username>/lights/<string:id>/name', methods=['PUT'])
def lightsPutName(username, id):
  jsonData = request.get_json(force=True)
  lights[id]["name"] = jsonData["name"]
  return ""

@app.route('/api/<string:username>/lights/<string:id>/state', methods=['PUT'])
def lightsPutState(username, id):
  jsonData = request.get_json(force=True)
  logger.debug(jsonData)
  for key, newValue in jsonData.items():
    oldValue = lights[id]["state"][key]
    if oldValue != newValue:
      handleLightStateUpdate(key, oldValue, newValue)
      lights[id]["state"][key] = jsonData[key]

  return ""

def handleLightStateUpdate(param, oldValue, newValue):
  logger.debug('handle update of %s from %s to %s', param, oldValue, newValue)

  if param == 'on':
    marantz.set_power(newValue)
  elif param == 'bri':
    marantz.set_volume( int(newValue / 255 * 50) )

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
    'ip': '192.168.0.x'
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