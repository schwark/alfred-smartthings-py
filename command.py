# encoding: utf-8

import sys
import re
import argparse
from workflow.workflow import MATCH_ATOM, MATCH_STARTSWITH, MATCH_SUBSTRING, MATCH_ALL, MATCH_INITIALS, MATCH_CAPITALS, MATCH_INITIALS_STARTSWITH, MATCH_INITIALS_CONTAIN
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_BURN, ICON_SWITCH, ICON_HOME, ICON_COLOR, ICON_INFO, ICON_SYNC, web, PasswordNotFound
from common import qnotify, error, st_api, get_device, get_scene

log = None

def get_devices(wf, api_key):
    """Retrieve all devices

    Returns a has of devices.

    """
    items = []
    i = 0
    while True:
        result = st_api(wf, api_key, 'devices', dict(max=200, page=i))
        if 'items' in result:
            items.extend(result['items'])
        if '_links' in result and 'next' in result['_links']:
            i += 1
        else:
            break

    return items

def get_scenes(wf, api_key):
    """Retrieve all scenes

    Returns a has of scenes.

    """
    return st_api(wf, api_key, 'scenes', dict(max=200))['items']

def get_colors():
    r = web.get('https://raw.githubusercontent.com/jonathantneal/color-names/master/color-names.json')
    flip_colors = r.json()
    colors = {v.lower().replace(' ',''): k for k, v in flip_colors.items()}
    return colors

def get_color(name, colors):
    name = name.lower().replace(' ','')
    if re.match('[0-9a-f]{6}', name):
        return '#'+name.upper()
    elif name in colors:
        return colors[name].upper()
    return ''

def get_device_capabilities(device):
    capabilities = []
    if device['components'] and len(device['components']) >  0 and \
        device['components'][0]['capabilities'] and len(device['components'][0]['capabilities']) > 0:
            capabilities = list(map( lambda x: x['id'], device['components'][0]['capabilities']))
    return capabilities

def get_device_commands(device, commands):
    result = []
    capabilities = get_device_capabilities(device)
    for capability in capabilities:
        for command, map in commands.items():
            if capability == map['capability']:
                result.append(command) 
    return result

def handle_device_commands(wf, api_key, args, commands):
    if not args.device_uid or args.device_command not in commands.keys():
        return 
    command = commands[args.device_command]

    device = get_device(wf, args.device_uid)
    device_name = device['label']
    capabilities = get_device_capabilities(device)
    if command['capability'] not in capabilities:
        error('Unsupported command for device')
        
    # eval all lambdas in arguments
    if 'arguments' in command and command['arguments']:
        for i, arg in enumerate(command['arguments']):
            if callable(arg):
                command['arguments'][i] = arg()
            elif isinstance(arg, dict):
                for key, value in arg.items():
                    if callable(value):
                        arg[key] = value()                

    data = {'commands': [command]}
    log.debug("Executing Switch Command: "+device_name+" "+args.device_command)
    result = st_api(wf, api_key,'devices/'+args.device_uid+'/commands', None, 'POST', data)
    result = (result and result['results']  and len(result['results']) > 0 and result['results'][0]['status'] and 'ACCEPTED' == result['results'][0]['status'])
    if result:
        qnotify("SmartThings", device_name+" turned "+args.device_command+' '+(args.device_params[0] if args.device_params else ''))
    log.debug("Switch Command "+device_name+" "+args.device_command+" "+(args.device_params[0] if args.device_params else '')+' '+("succeeded" if result else "failed"))
    return result

def handle_scene_commands(wf, api_key, args):
    if not args.scene_uid:
        return 
    scene = get_scene(wf, args.scene_uid)
    scene_name = scene['sceneName']
    log.debug("Executing Scene Command: "+scene_name)
    result = st_api(wf, api_key,'scenes/'+args.scene_uid+'/execute', None, 'POST')
    result = (result and result['status'] and 'success' == result['status'])
    if result:
        qnotify("SmartThings", "Ran "+scene_name)
    log.debug("Scene Command "+scene_name+" "+("succeeded" if result else "failed"))
    return result

def main(wf):
    # retrieve cached devices and scenes
    devices = wf.stored_data('devices')
    scenes = wf.stored_data('scenes')
    colors = wf.stored_data('colors')

    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
    # add an optional (nargs='?') --apikey argument and save its
    # value to 'apikey' (dest). This will be called from a separate "Run Script"
    # action with the API key
    parser.add_argument('--apikey', dest='apikey', nargs='?', default=None)
    parser.add_argument('--showstatus', dest='showstatus', nargs='?', default=None)
    # add an optional (nargs='?') --update argument and save its
    # value to 'apikey' (dest). This will be called from a separate "Run Script"
    # action with the API key
    parser.add_argument('--update', dest='update', action='store_true', default=False)
    # reinitialize 
    parser.add_argument('--reinit', dest='reinit', action='store_true', default=False)
    # device name, uid, command and any command params
    parser.add_argument('--device-uid', dest='device_uid', default=None)
    parser.add_argument('--device-command', dest='device_command', default='')
    parser.add_argument('--device-params', dest='device_params', nargs='*', default=[])
    # scene name, uid, command and any command params
    parser.add_argument('--scene-uid', dest='scene_uid', default=None)

    # add an optional query and save it to 'query'
    parser.add_argument('query', nargs='?', default=None)
    # parse the script's arguments
    args = parser.parse_args(wf.args)

    log.debug("args are "+str(args))

    words = args.query.split(' ') if args.query else []

    # list of commands
    commands = {
        'status': {
            'capability': 'global'
        },
        'on': {
                'component': 'main',
                'capability': 'switch',
                'command': 'on'
        }, 
        'off': {
                'component': 'main',
                'capability': 'switch',
                'command': 'off'
        },
        'dim': {
                'component': 'main',
                'capability': 'switchLevel',
                'command': 'setLevel',
                'arguments': [
                    lambda: int(args.device_params[0]),
                ]
        },
        'lock': {
                'component': 'main',
                'capability': 'lock',
                'command': 'lock'
        }, 
        'unlock': {
                'component': 'main',
                'capability': 'lock',
                'command': 'unlock'
        },
        'color': {
                'component': 'main',
                'capability': 'colorControl',
                'command': 'setColor',
                'arguments': [
                    {
                        'hex': lambda: get_color(args.device_params[0], colors)
                    }
                ]
        },
        'mode': {
            'component': 'main',
            'capability': 'thermostatMode',
            'command': 'setThermostatMode',
            'arguments': [
                lambda: str(args.device_params[0])
            ]
        },
        'heat': {
                'component': 'main',
                'capability': 'thermostatHeatingSetpoint',
                'command': 'setHeatingSetpoint',
                'arguments': [
                    lambda: int(args.device_params[0]),
                ]
        },
        'cool': {
                'component': 'main',
                'capability': 'thermostatCoolingSetpoint',
                'command': 'setCoolingSetpoint',
                'arguments': [
                    lambda: int(args.device_params[0]),
                ]
        }
    }

    # Reinitialize if necessary
    if args.reinit:
        wf.reset()
        wf.delete_password('smartthings_api_key')
        qnotify('SmartThings', 'Workflow reinitialized')
        return 0

    if args.showstatus:
        if args.showstatus in ['on', 'off']:
            wf.settings['showstatus'] = args.showstatus
            wf.settings.save()
            qnotify('SmartThings', 'Show Status '+args.showstatus)
        return 0

    ####################################################################
    # Save the provided API key
    ####################################################################

    # save API key if that is passed in
    if args.apikey:  # Script was passed an API key
        log.debug("saving api key "+args.apikey)
        # save the key
        wf.save_password('smartthings_api_key', args.apikey)
        qnotify('SmartThings', 'API Key Saved')
        return 0  # 0 means script exited cleanly

    ####################################################################
    # Check that we have an API key saved
    ####################################################################

    try:
        api_key = wf.get_password('smartthings_api_key')
    except PasswordNotFound:  # API key has not yet been set
        error('API Key not found')
        return 0

    # Update devices if that is passed in
    if args.update:  
        # update devices and scenes
        devices = get_devices(wf, api_key)
        scenes = get_scenes(wf, api_key)
        colors = get_colors()
        wf.store_data('devices', devices)
        wf.store_data('scenes', scenes)
        wf.store_data('colors', colors)
        qnotify('SmartThings', 'Devices and Scenes updated')
        return 0  # 0 means script exited cleanly

   # handle any device or scene commands there may be
    handle_device_commands(wf, api_key, args, commands)
    handle_scene_commands(wf, api_key, args)


if __name__ == u"__main__":
    wf = Workflow(update_settings={
        'github_slug': 'schwark/alfred-smartthings-py'
    })
    log = wf.logger
    sys.exit(wf.run(main))
    