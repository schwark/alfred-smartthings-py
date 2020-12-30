# encoding: utf-8

import sys
import re
import argparse
import json
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_SWITCH, ICON_HOME, ICON_COLOR, ICON_INFO, ICON_SYNC, web, PasswordNotFound

log = None

def qnotify(title, text):
    print(text)

def error(text):
    print(text)
    exit(0)

def get_device(device_uid):
    devices = wf.stored_data('devices')
    return next((x for x in devices if device_uid == x['deviceId']), None)

def get_scene(scene_uid):
    scenes = wf.stored_data('scenes')
    return next((x for x in scenes if scene_uid == x['sceneId']), None)

def st_api(api_key, url, params=None, method='GET', data=None):
    url = 'https://api.smartthings.com/v1/'+url
    headers = {'Authorization':'Bearer '+api_key,'Accept':"application/json"}
    r = None

    if('GET' == method):
        r = web.get(url, params, headers)
    else:
        headers['Content-type'] = "application/json"
        if data and isinstance(data, dict):
            data = json.dumps(data)
        log.debug("posting with data "+data)
        r = web.post(url, params, data, headers)

    log.debug("st_api: url:"+url+", method: "+method+",  headers: "+str(headers)+", params: "+str(params)+", data: "+str(data))
    # throw an error if request failed
    # Workflow will catch this and show it to the user
    r.raise_for_status()

    # Parse the JSON returned by pinboard and extract the posts
    result = r.json()
    #log.debug(str(result))
    return result    

def get_devices(api_key):
    """Retrieve all devices

    Returns a has of devices.

    """
    items = []
    i = 0
    while True:
        result = st_api(api_key, 'devices', dict(max=200, page=i))
        if 'items' in result:
            items.extend(result['items'])
        if '_links' in result and 'next' in result['_links']:
            i += 1
        else:
            break

    return items

def get_scenes(api_key):
    """Retrieve all scenes

    Returns a has of scenes.

    """
    return st_api(api_key, 'scenes', dict(max=200))['items']

def get_color(name):
    colors = {
        "aliceblue": "#f0f8ff",
        "antiquewhite": "#faebd7",
        "aqua": "#00ffff",
        "aquamarine": "#7fffd4",
        "azure": "#f0ffff",
        "beige": "#f5f5dc",
        "bisque": "#ffe4c4",
        "black": "#000000",
        "blanchedalmond": "#ffebcd",
        "blue": "#0000ff",
        "blueviolet": "#8a2be2",
        "brown": "#a52a2a",
        "burlywood": "#deb887",
        "cadetblue": "#5f9ea0",
        "chartreuse": "#7fff00",
        "chocolate": "#d2691e",
        "coral": "#ff7f50",
        "cornflowerblue": "#6495ed",
        "cornsilk": "#fff8dc",
        "crimson": "#dc143c",
        "cyan": "#00ffff",
        "darkblue": "#00008b",
        "darkcyan": "#008b8b",
        "darkgoldenrod": "#b8860b",
        "darkgray": "#a9a9a9",
        "darkgreen": "#006400",
        "darkgrey": "#a9a9a9",
        "darkkhaki": "#bdb76b",
        "darkmagenta": "#8b008b",
        "darkolivegreen": "#556b2f",
        "darkorange": "#ff8c00",
        "darkorchid": "#9932cc",
        "darkred": "#8b0000",
        "darksalmon": "#e9967a",
        "darkseagreen": "#8fbc8f",
        "darkslateblue": "#483d8b",
        "darkslategray": "#2f4f4f",
        "darkslategrey": "#2f4f4f",
        "darkturquoise": "#00ced1",
        "darkviolet": "#9400d3",
        "deeppink": "#ff1493",
        "deepskyblue": "#00bfff",
        "dimgray": "#696969",
        "dimgrey": "#696969",
        "dodgerblue": "#1e90ff",
        "firebrick": "#b22222",
        "floralwhite": "#fffaf0",
        "forestgreen": "#228b22",
        "fuchsia": "#ff00ff",
        "gainsboro": "#dcdcdc",
        "ghostwhite": "#f8f8ff",
        "goldenrod": "#daa520",
        "gold": "#ffd700",
        "gray": "#808080",
        "green": "#008000",
        "greenyellow": "#adff2f",
        "grey": "#808080",
        "honeydew": "#f0fff0",
        "hotpink": "#ff69b4",
        "indianred": "#cd5c5c",
        "indigo": "#4b0082",
        "ivory": "#fffff0",
        "khaki": "#f0e68c",
        "lavenderblush": "#fff0f5",
        "lavender": "#e6e6fa",
        "lawngreen": "#7cfc00",
        "lemonchiffon": "#fffacd",
        "lightblue": "#add8e6",
        "lightcoral": "#f08080",
        "lightcyan": "#e0ffff",
        "lightgoldenrodyellow": "#fafad2",
        "lightgray": "#d3d3d3",
        "lightgreen": "#90ee90",
        "lightgrey": "#d3d3d3",
        "lightpink": "#ffb6c1",
        "lightsalmon": "#ffa07a",
        "lightseagreen": "#20b2aa",
        "lightskyblue": "#87cefa",
        "lightslategray": "#778899",
        "lightslategrey": "#778899",
        "lightsteelblue": "#b0c4de",
        "lightyellow": "#ffffe0",
        "lime": "#00ff00",
        "limegreen": "#32cd32",
        "linen": "#faf0e6",
        "magenta": "#ff00ff",
        "maroon": "#800000",
        "mediumaquamarine": "#66cdaa",
        "mediumblue": "#0000cd",
        "mediumorchid": "#ba55d3",
        "mediumpurple": "#9370db",
        "mediumseagreen": "#3cb371",
        "mediumslateblue": "#7b68ee",
        "mediumspringgreen": "#00fa9a",
        "mediumturquoise": "#48d1cc",
        "mediumvioletred": "#c71585",
        "midnightblue": "#191970",
        "mintcream": "#f5fffa",
        "mistyrose": "#ffe4e1",
        "moccasin": "#ffe4b5",
        "navajowhite": "#ffdead",
        "navy": "#000080",
        "oldlace": "#fdf5e6",
        "olive": "#808000",
        "olivedrab": "#6b8e23",
        "orange": "#ffa500",
        "orangered": "#ff4500",
        "orchid": "#da70d6",
        "palegoldenrod": "#eee8aa",
        "palegreen": "#98fb98",
        "paleturquoise": "#afeeee",
        "palevioletred": "#db7093",
        "papayawhip": "#ffefd5",
        "peachpuff": "#ffdab9",
        "peru": "#cd853f",
        "pink": "#ffc0cb",
        "plum": "#dda0dd",
        "powderblue": "#b0e0e6",
        "purple": "#800080",
        "rebeccapurple": "#663399",
        "red": "#ff0000",
        "rosybrown": "#bc8f8f",
        "royalblue": "#4169e1",
        "saddlebrown": "#8b4513",
        "salmon": "#fa8072",
        "sandybrown": "#f4a460",
        "seagreen": "#2e8b57",
        "seashell": "#fff5ee",
        "sienna": "#a0522d",
        "silver": "#c0c0c0",
        "skyblue": "#87ceeb",
        "slateblue": "#6a5acd",
        "slategray": "#708090",
        "slategrey": "#708090",
        "snow": "#fffafa",
        "springgreen": "#00ff7f",
        "steelblue": "#4682b4",
        "tan": "#d2b48c",
        "teal": "#008080",
        "thistle": "#d8bfd8",
        "tomato": "#ff6347",
        "turquoise": "#40e0d0",
        "violet": "#ee82ee",
        "wheat": "#f5deb3",
        "white": "#ffffff",
        "whitesmoke": "#f5f5f5",
        "yellow": "#ffff00",
        "yellowgreen": "#9acd32"
    }
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

def handle_config(args):
    if not args.query:
        log.debug('handle_config: no query passed in')
        return
    words = args.query.split()
    log.debug('handle_config: words = '+'/'.join(words))
    if('apikey' == words[0] and len(words) > 1):
        wf.add_item(title='Set API Key...',
                    subtitle='Setting API Key to '+words[1],
                    arg='--apikey "'+words[1]+'"',
                    valid=True,
                    icon=ICON_INFO)
        wf.send_feedback()
        return True
    if('update' == words[0]):
        wf.add_item(title='Update Devices and Scenes...',
                    subtitle='Refresh Devices and Scenes',
                    arg='--update',
                    valid=True,
                    icon=ICON_SYNC)
        wf.send_feedback()
        return True
    if('reinit' == words[0]):
        wf.add_item(title='Reinitialize the workflow...',
                    subtitle='CAUTION: Forgets all API Keys, Devices and Scenes',
                    arg='--reinit',
                    valid=True,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return True
    return False

def get_device_commands(device, commands):
    result = []
    capabilities = get_device_capabilities(device)
    for capability in capabilities:
        for command, map in commands.items():
            if capability == map['capability']:
                result.append(command) 
    return result

def handle_device_commands(api_key, args, commands):
    if not args.device_uid or args.device_command not in commands.keys():
        return 
    command = commands[args.device_command]

    device = get_device(args.device_uid)
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
    result = st_api(api_key,'devices/'+args.device_uid+'/commands', None, 'POST', data)
    result = (result and result['results']  and len(result['results']) > 0 and result['results'][0]['status'] and 'ACCEPTED' == result['results'][0]['status'])
    if result:
        qnotify("SmartThings", device_name+" turned "+args.device_command)
    log.debug("Switch Command "+device_name+" "+args.device_command+" "+("succeeded" if result else "failed"))
    return result

def handle_scene_commands(api_key, args):
    if not args.scene_uid:
        return 
    scene = get_scene(args.scene_uid)
    scene_name = scene['sceneName']
    log.debug("Executing Scene Command: "+scene_name)
    result = st_api(api_key,'scenes/'+args.scene_uid+'/execute', None, 'POST')
    result = (result and result['status'] and 'success' == result['status'])
    if result:
        qnotify("SmartThings", "Ran "+scene_name)
    log.debug("Scene Command "+scene_name+" "+("succeeded" if result else "failed"))
    return result


def extract_commands(args, wf, devices, commands):
    words = args.query.split() if args.query else []
    full_devices = wf.filter(args.query, devices, key=lambda x: search_key_for_device(x, commands), min_score=20)
    minusone_devices = wf.filter(' '.join(words[0:-1]), devices, key=lambda x: search_key_for_device(x, commands), min_score=20)
    minustwo_devices = wf.filter(' '.join(words[0:-2]), devices, key=lambda x: search_key_for_device(x, commands), min_score=20)
    if 1 == len(minusone_devices) and 0 == len(full_devices):
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
    return args

def main(wf):
    # list of commands
    commands = {
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
                        'hex': lambda: get_color(args.device_params[0])
                    }
                ]
        }
    }

    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
    # add an optional (nargs='?') --apikey argument and save its
    # value to 'apikey' (dest). This will be called from a separate "Run Script"
    # action with the API key
    parser.add_argument('--apikey', dest='apikey', nargs='?', default=None)
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

    # check to see if any config commands - non device/scene commands are needed
    if(handle_config(args)):
        # if command was  handled, exit cleanly  now
        return 0

    # Reinitialize if necessary
    if args.reinit:
        wf.reset()
        wf.delete_password('smartthings_api_key')
        qnotify('SmartThings', 'Workflow reinitialized')
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
        wf.add_item('No API key set...',
                    'Please use st apikey to set your SmartThings API key.',
                    valid=False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Update devices if that is passed in
    if args.update:  
        # update devices and scenes
        devices = get_devices(api_key)
        scenes = get_scenes(api_key)
        wf.store_data('devices', devices)
        wf.store_data('scenes', scenes)
        qnotify('SmartThings', 'Devices and Scenes updated')
        return 0  # 0 means script exited cleanly

   # handle any device or scene commands there may be
    handle_device_commands(api_key, args, commands)
    handle_scene_commands(api_key, args)

    # retrieve cached devices and scenes
    devices = wf.stored_data('devices')
    scenes = wf.stored_data('scenes')

    # since this i now sure to be a device/scene query, fix args if there is a device/scene command in there
    args = extract_commands(args, wf, devices, commands)
 
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
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0
    if not scenes:
        scenes = dict()

    # If script was passed a query, use it to filter posts
    if query:
        devices = wf.filter(query, devices, key=lambda x: search_key_for_device(x, commands), min_score=20)
        scenes = wf.filter(query, scenes, key=search_key_for_scene, min_score=20)

        if devices:
            if len(devices) > 1:
                # Loop through the returned devices and add an item for each to
                # the list of results for Alfred
                for device in devices:
                    wf.add_item(title=device['label'],
                            subtitle='Turn '+device['label']+' '+args.device_command+' '+(' '.join(args.device_params) if args.device_params else ''),
                            arg=' --device-uid '+device['deviceId']+' --device-command '+args.device_command+' --device-params '+(' '.join(args.device_params)),
                            autocomplete=device['label'],
                            valid=args.device_command in commands,
                            icon=ICON_SWITCH)
            elif not args.device_command or args.device_command not in commands:
                # Single device only, no command or not complete command yet so populate with all the commands
                device = devices[0]
                device_commands = get_device_commands(device, commands)
                device_commands = list(filter(lambda x: x.startswith(args.device_command), device_commands))
                for command in device_commands:
                    wf.add_item(title=device['label'],
                            subtitle='Turn '+device['label']+' '+command+' '+(' '.join(args.device_params) if args.device_params else ''),
                            arg=' --device-uid '+device['deviceId']+' --device-command '+command+' --device-params '+(' '.join(args.device_params)),
                            autocomplete=device['label']+' '+command,
                            valid='arguments' not in commands[command] or args.device_params,
                            icon=ICON_SWITCH)
            else:
                # single device and has command already - populate with params?
                device = devices[0]
                wf.add_item(title=device['label'],
                        subtitle='Turn '+device['label']+' '+args.device_command+' '+(' '.join(args.device_params) if args.device_params else ''),
                        arg=' --device-uid '+device['deviceId']+' --device-command '+args.device_command+' --device-params '+(' '.join(args.device_params)),
                        autocomplete=device['label']+' '+args.device_command,
                        valid='arguments' not in commands[args.device_command] or args.device_params,
                        icon=ICON_SWITCH)

        # Loop through the returned scenes and add an item for each to
        # the list of results for Alfred
        for scene in scenes:
            wf.add_item(title=scene['sceneName'],
                    subtitle='Run '+scene['sceneName'],
                    arg=' --scene-uid '+scene['sceneId'],
                    autocomplete=scene['sceneName'],
                    valid=True,
                    icon=ICON_COLOR)

        # Send the results to Alfred as XML
        wf.send_feedback()
    return 0


if __name__ == u"__main__":
    wf = Workflow(update_settings={
        'github_slug': 'schwark/alfred-smartthings-py'
    })
    log = wf.logger
    sys.exit(wf.run(main))
    