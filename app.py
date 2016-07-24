from AppFramework import App, JsonResponse
from config import Configurator
from bridgedata import BridgeData, BridgeDataJSONEncoder, ExtendedColorLight, DimmableLight
from marantz import MarantzIp
import MarantzLightAdapter

import logging
import json

app = App(__name__)

@app.route('/?')
def index(request):
    return "Welcome to the Marantz Hue adapter. Control you marantz receiver as if it were a Hue Light!"

@app.route('/api/config/?', 'GET')
def api_config(request):
    return JsonResponse( bridgeData.config )

@app.route('/api/?', 'POST')
def create_user(request):
    return JsonResponse( [ { "success": { "username": config['HueBridge']['user'] } } ] )

@app.route('/api/(\w+)', 'GET')
def api_username(request, username):
    if(username == "null"):
        return JsonResponse( [ { "error": { "type": 1, "address": "/", "description": "unauthorized user" } } ] )
    else:
        return JsonResponse( bridgeData.data, BridgeDataJSONEncoder )

@app.route('/api/(\w+)/lights/(\w+)/name', 'PUT')
def lightsPutName(request, username, id):
    jsonData = json.loads(request.data)
    bridgeData.lights[id].name = jsonData["name"]
    return ""

@app.route('/api/(\w+)/lights/(\w+)/state', 'PUT')
def lightsPutState(request, username, id):
    jsonData = json.loads(request.data)
    logger.debug(jsonData)
    for key, newValue in jsonData.items():
        oldValue = bridgeData.lights[id].state[key]
        if oldValue != newValue:
            bridgeData.lights[id].set_state_property(key, jsonData[key])
    return ""

if __name__ == '__main__':
    # init logging
    logging.config.fileConfig('log.cfg')
    logger = logging.getLogger('server')

    logger.info('Starting marantz-hue-adapter server')
    config = Configurator().config

    marantzIp = MarantzIp( (config['Marantz']['host'], int(config['Marantz']['port'])) )
    bridgeData = BridgeData( config )
    bridgeData.lights['1'] = ExtendedColorLight('Marantz FM', 'uniqfmradio')
    bridgeData.lights['2'] = DimmableLight('Marantz Media Player', 'uniqmediaplayer')
    
    MarantzLightAdapter.MarantzFmRadioLightAdapter( config, bridgeData.lights['1'], marantzIp )
    MarantzLightAdapter.MarantzMediaPlayerLightAdapter( config, bridgeData.lights['2'], marantzIp )
    app.start(host=config['Server']['host'], port=int(config['Server']['port']), debug=True)