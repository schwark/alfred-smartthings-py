# encoding: utf-8

import sys
import re
import argparse
from workflow.workflow import MATCH_ATOM, MATCH_STARTSWITH, MATCH_SUBSTRING, MATCH_ALL, MATCH_INITIALS, MATCH_CAPITALS, MATCH_INITIALS_STARTSWITH, MATCH_INITIALS_CONTAIN
from workflow import Workflow, ICON_WEB, ICON_NOTE, ICON_BURN, ICON_SWITCH, ICON_HOME, ICON_COLOR, ICON_INFO, ICON_SYNC, web, PasswordNotFound
from common import st_api, get_stored_data

log = None

def get_device_icon(device):
    capabilities = get_device_capabilities(device)
    if 'thermostatMode' in capabilities:
        icon = 'thermostat'
    elif 'lock' in capabilities:
        icon = 'lock'
    elif 'colorControl' in capabilities:
        icon = 'color-light'
    elif 'switchLevel' in capabilities:
        icon = 'light'
    elif 'windowShade' in capabilities:
        icon = 'shade'
    elif 'contactSensor' in capabilities:
        icon = 'contact'
    else:
        icon = 'switch'
    return 'icons/'+icon+'.png'

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

def search_key_for_device(device, commands):
    """Generate a string search key for a switch"""
    elements = []
    supported_capabilities = set(map(lambda x: x[1]['capability'], commands.items()))
    #log.debug("supported capabilities are : "+str(supported_capabilities))
    capabilities = get_device_capabilities(device)
    if len(list(set(capabilities) & supported_capabilities)) > 0:
        elements.append(device['label'])  # label of device
    return u' '.join(elements)

def search_key_for_scene(scene):
    """Generate a string search key for a scene"""
    elements = []
    elements.append(scene['sceneName'])  # name of scene
    return u' '.join(elements)

def add_config_commands(args, config_commands):
    word = args.query.lower().split(' ')[0] if args.query else ''
    config_command_list = wf.filter(word, config_commands.keys(), min_score=80, match_on=MATCH_SUBSTRING | MATCH_STARTSWITH | MATCH_ATOM)
    if config_command_list:
        for cmd in config_command_list:
            wf.add_item(config_commands[cmd]['title'],
                        config_commands[cmd]['subtitle'],
                        arg=config_commands[cmd]['args'],
                        autocomplete=config_commands[cmd]['autocomplete'],
                        icon=config_commands[cmd]['icon'],
                        valid=config_commands[cmd]['valid'])
    return config_command_list

def get_device_commands(wf, device, commands):
    result = []
    capabilities = get_device_capabilities(device)
    if not should_show_status(wf):
        capabilities.append('global')
    for capability in capabilities:
        for command, map in commands.items():
            if capability == map['capability']:
                result.append(command) 
    return result

def get_filtered_devices(wf, query, devices, commands):
    result = wf.filter(query, devices, key=lambda x: search_key_for_device(x, commands), min_score=80, match_on=MATCH_SUBSTRING | MATCH_STARTSWITH | MATCH_ATOM)
    # check to see if the first one is an exact match - if yes, remove all the other results
    if result and query and 'label' in result[0] and result[0]['label'] and result[0]['label'].lower() == query.lower():
        result = result[0:1]
    return result

def extract_commands(wf, args, devices, commands):
    words = args.query.split() if args.query else []
    args.device_command = ''
    args.device_params = []
    if devices:
        full_devices = get_filtered_devices(wf, args.query,  devices, commands)
        minusone_devices = get_filtered_devices(wf, ' '.join(words[0:-1]),  devices, commands)
        minustwo_devices = get_filtered_devices(wf, ' '.join(words[0:-2]),  devices, commands)

        if 1 == len(minusone_devices) and (0 == len(full_devices) or (1 == len(full_devices) and full_devices[0]['deviceId'] == minusone_devices[0]['deviceId'])):
            extra_words = args.query.replace(minusone_devices[0]['label'],'').split()
            if extra_words:
                log.debug("extract_commands: setting command to "+extra_words[0])
                args.device_command = extra_words[0]
                args.query = minusone_devices[0]['label']
        if 1 == len(minustwo_devices) and 0 == len(full_devices) and 0 == len(minusone_devices):
            extra_words = args.query.replace(minustwo_devices[0]['label'],'').split()
            if extra_words:
                args.device_command = extra_words[0]
                args.query = minustwo_devices[0]['label']
                args.device_params = extra_words[1:]
        log.debug("extract_commands: "+str(args))
    return args

def device_status(wf, api_key, device):
    caps = {
        'switch': {
            'tag': 'switch',
            'icon': u'🎚'
        },
        'switchLevel': {
            'tag': 'level',
            'icon': u'💡'
        },
        'lock': {
            'tag': 'lock',
            'icon': u'🔒'
        },
        'battery': {
            'tag': 'battery',
            'icon': u'🔋'
        },
        'colorControl': {
            'tag': 'color',
            'icon': u'🎨'
        },
        'windowShade': {
            'tag': 'windowShade',
            'icon': u'🪟'
        },
        'windowShadeLevel': {
            'tag': 'shadeLevel',
            'icon': u'🌒'
        },
        'contactSensor': {
            'tag': 'contact',
            'icon': u'🔓'
        },
        'thermostat': [
        {
            'tag': 'heatingSetpoint',
            'icon': u'🔥'
        },
        {
            'tag': 'coolingSetpoint',
            'icon': u'❄️'
        },
        {
            'tag': 'thermostatOperatingState',
            'icon': u'🏃🏻‍♀️'
        },
        {
            'tag': 'temperature',
            'icon': u'🌡'
        },
        {
            'tag': 'thermostatFanMode',
            'icon': u'💨'
        },
        {
            'tag': 'thermostatMode',
            'icon': u'😰'
        }
        ]
    }
    subtitle = ''
    status = st_api(wf, api_key, '/devices/'+device['deviceId']+'/status')
    if status and 'components' in status and 'main' in status['components']:
        detail = status['components']['main']
        for cap in caps:
            if not cap in detail: continue
            metas = caps[cap]
            if not isinstance(metas, list):
                metas = [metas]
            for meta in metas:
                tag = meta['tag']
                if not tag in detail[cap]: continue
                log.debug(device['label']+' '+cap+' '+tag)
                subtitle += u'  '+meta['icon']+' '+str(detail[cap][tag]['value'])+(detail[cap][tag]['unit'] if 'unit' in detail[cap][tag] else '')
    return subtitle

def should_show_status(wf):
    return ('on' == wf.settings['showstatus']) if 'showstatus' in wf.settings else False

def main(wf):
    # retrieve cached devices and scenes
    devices = get_stored_data(wf, 'devices')
    scenes = get_stored_data(wf, 'scenes')
    colors = get_stored_data(wf, 'colors')

    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
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
        'toggle': {
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
        'slevel': {
                'component': 'main',
                'capability': 'windowShadeLevel',
                'command': 'setShadeLevel',
                'arguments': [
                    lambda: int(args.device_params[0]),
                ]
        },
        'open': {
                'component': 'main',
                'capability': 'windowShade',
                'command': 'open'
        },
        'close': {
                'component': 'main',
                'capability': 'windowShade',
                'command': 'close'
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
        'view': {
                'component': 'main',
                'capability': 'contactSensor',
                'command': 'view'
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

    command_params = {
        'color': {
            'values': colors.keys() if colors else [],
            'regex': '[0-9a-f]{6}'
        },
        'mode': {
            'values': ['auto','heat','cool','off']
        }
    }

    config_commands = {
        'update': {
            'title': 'Update Devices and Scenes',
            'subtitle': 'Update the devices and scenes from SmartThings',
            'autocomplete': 'update',
            'args': ' --update',
            'icon': ICON_SYNC,
            'valid': True
        },
        'apikey': {
            'title': 'Set API Key',
            'subtitle': 'Set api key to personal access token from SmartThings',
            'autocomplete': 'apikey',
            'args': ' --apikey '+(words[1] if len(words)>1 else ''),
            'icon': ICON_WEB,
            'valid': len(words) > 1
        },
        'showstatus': {
            'title': 'Turn on/off showing of status when single device',
            'subtitle': 'Adds latency. When off, can still get info via status command',
            'autocomplete': 'showstatus',
            'args': ' --showstatus '+(words[1] if len(words)>1 else ''),
            'icon': ICON_INFO,
            'valid': len(words) > 1 and words[1] in ['on', 'off']
        },
        'reinit': {
            'title': 'Reinitialize the workflow',
            'subtitle': 'CAUTION: this deletes all scenes, devices and apikeys...',
            'autocomplete': 'reinit',
            'args': ' --reinit',
            'icon': ICON_BURN,
            'valid': True
        },
        'workflow:update': {
            'title': 'Update the workflow',
            'subtitle': 'Updates workflow to latest github version',
            'autocomplete': 'workflow:update',
            'args': '',
            'icon': ICON_SYNC,
            'valid': True
        }
    }

    # add config commands to filter
    add_config_commands(args, config_commands)

    ####################################################################
    # Check that we have an API key saved
    ####################################################################

    try:
        api_key = wf.get_password('smartthings_api_key')
    except PasswordNotFound:  # API key has not yet been set
        wf.add_item('No API key set...',
                    'Please use st apikey to set your SmartThings API key.',
                    valid=False,
                    icon=ICON_NOTE)
        wf.send_feedback()
        return 0

    # since this i now sure to be a device/scene query, fix args if there is a device/scene command in there
    args = extract_commands(wf, args, devices, commands)
 
    # update query post extraction
    query = args.query


    ####################################################################
    # View/filter devices or scenes
    ####################################################################

    # Check for an update and if available add an item to results
    if wf.update_available:
        # Add a notification to top of Script Filter results
        wf.add_item('New version available',
            'Action this item to install the update',
            autocomplete='workflow:update',
            icon=ICON_INFO)


    if not devices or len(devices) < 1:
        wf.add_item('No Devices...',
                    'Please use st update - to update your SmartThings devices.',
                    valid=False,
                    icon=ICON_NOTE)
        wf.send_feedback()
        return 0
    if not scenes:
        scenes = dict()

    # If script was passed a query, use it to filter posts
    if query:
        devices = get_filtered_devices(wf, query, devices, commands)
        scenes = wf.filter(query, scenes, key=search_key_for_scene, min_score=80, match_on=MATCH_SUBSTRING | MATCH_STARTSWITH | MATCH_ATOM)

        if devices:
            if 1 == len(devices) and should_show_status(wf):
                device = devices[0]
                wf.add_item(title=device['label'],
                        subtitle=device_status(wf, api_key, device),
                        arg=' --device-uid '+device['deviceId']+' --device-command '+args.device_command,
                        autocomplete=device['label']+' '+args.device_command,
                        valid=False,
                        icon=get_device_icon(device))
            if 1 == len(devices) and (not args.device_command or args.device_command not in commands):
                # Single device only, no command or not complete command yet so populate with all the commands
                device = devices[0]
                device_commands = get_device_commands(wf, device, commands)
                device_commands = list(filter(lambda x: x.startswith(args.device_command), device_commands))
                log.debug('args.device_command is '+args.device_command)
                for command in device_commands:
                    wf.add_item(title=device['label'],
                            subtitle='Turn '+device['label']+' '+command+' '+(' '.join(args.device_params) if args.device_params else ''),
                            arg=' --device-uid '+device['deviceId']+' --device-command '+command+' --device-params '+(' '.join(args.device_params)),
                            autocomplete=device['label']+' '+command,
                            valid=bool('status' != command and ('arguments' not in commands[command] or args.device_params)),
                            icon=get_device_icon(device))
            elif 1 == len(devices) and (args.device_command and args.device_command in commands and args.device_command in command_params):
                # single device and has command already - populate with params?
                device = devices[0]
                param_list = command_params[args.device_command]['values']
                param_start = args.device_params[0] if args.device_params else ''
                param_list = list(filter(lambda x: x.startswith(param_start), param_list))
                param_list.sort()
                check_regex = False
                if not param_list and command_params[args.device_command]['regex']:
                    param_list.append(args.device_params[0].lower())
                    check_regex = True
                for param in param_list:
                    wf.add_item(title=device['label'],
                            subtitle='Turn '+device['label']+' '+args.device_command+' '+param,
                            arg=' --device-uid '+device['deviceId']+' --device-command '+args.device_command+' --device-params '+param,
                            autocomplete=device['label']+' '+args.device_command,
                            valid=bool(not check_regex or re.match(command_params[args.device_command]['regex'], param)),
                            icon=get_device_icon(device))
            elif 1 == len(devices) and ('status' == args.device_command):
                device = devices[0]
                wf.add_item(title=device['label'],
                        subtitle=device_status(wf, api_key, device),
                        arg=' --device-uid '+device['deviceId']+' --device-command '+args.device_command,
                        autocomplete=device['label']+' '+args.device_command,
                        valid=False,
                        icon=get_device_icon(device))
            else:
                # Loop through the returned devices and add an item for each to
                # the list of results for Alfred
                for device in devices:
                    wf.add_item(title=device['label'],
                            subtitle='Turn '+device['label']+' '+args.device_command+' '+(' '.join(args.device_params) if args.device_params else ''),
                            arg=' --device-uid '+device['deviceId']+' --device-command '+args.device_command+' --device-params '+(' '.join(args.device_params)),
                            autocomplete=device['label'],
                            valid=bool(args.device_command in commands),
                            icon=get_device_icon(device))


        # Loop through the returned scenes and add an item for each to
        # the list of results for Alfred
        for scene in scenes:
            wf.add_item(title=scene['sceneName'],
                    subtitle='Run '+scene['sceneName'],
                    arg=' --scene-uid '+scene['sceneId'],
                    autocomplete=scene['sceneName'],
                    valid=True,
                    icon='icons/scene.png')

        # Send the results to Alfred as XML
        wf.send_feedback()
    return 0


if __name__ == u"__main__":
    wf = Workflow(update_settings={
        'github_slug': 'schwark/alfred-smartthings-py'
    })
    log = wf.logger
    sys.exit(wf.run(main))
    