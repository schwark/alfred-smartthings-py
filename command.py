# encoding: utf-8

import sys
import re
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_SWITCH, ICON_HOME, ICON_COLOR, ICON_INFO, ICON_SYNC, web, PasswordNotFound

log = None
__version__ = '1.0.3'

def qnotify(title, text):
    print(text)

def st_api(api_key, url, params=None, method='GET', data=None):
    url = 'https://api.smartthings.com/v1/'+url
    headers = dict(Authorization='Bearer '+api_key)
    r = None

    if('GET' == method):
        r = web.get(url, params, headers)
    else:
        r = web.post(url, params, data, headers)

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
    return st_api(api_key, 'devices', dict(max=10000))['items']

def get_scenes(api_key):
    """Retrieve all scenes

    Returns a has of scenes.

    """
    return st_api(api_key, 'scenes', dict(max=10000))['items']

def search_key_for_switch(device):
    """Generate a string search key for a switch"""
    elements = []
    if device['components'] and len(device['components']) >  0 and \
        device['components'][0]['capabilities'] and len(device['components'][0]['capabilities']) > 1 and \
            'switch' == device['components'][0]['capabilities'][0]['id']:
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

def handle_switch_commands(api_key, args, commands):
    if not args.device_uid or args.device_command not in commands:
        return 
    data = """{{
"commands": [
{{
    "component": "main",
    "capability": "switch",
    "command": "{cmd}"
}}
]
}}""".format(cmd=args.device_command)
    log.debug("Executing Switch Command: "+args.device_name+" "+args.device_command)
    result = st_api(api_key,'devices/'+args.device_uid+'/commands', None, 'POST', data)
    result = (result and result['results']  and len(result['results']) > 0 and result['results'][0]['status'] and 'ACCEPTED' == result['results'][0]['status'])
    if result:
        qnotify("SmartThings", args.device_name+" turned "+args.device_command)
    log.debug("Switch Command "+args.device_name+" "+args.device_command+" "+("succeeded" if result else "failed"))
    return result

def handle_scene_commands(api_key, args):
    if not args.scene_uid:
        return 
    log.debug("Executing Scene Command: "+args.scene_name)
    result = st_api(api_key,'scenes/'+args.scene_uid+'/execute', None, 'POST')
    result = (result and result['status'] and 'success' == result['status'])
    if result:
        qnotify("SmartThings", "Ran "+args.scene_name)
    log.debug("Scene Command "+args.scene_name+" "+("succeeded" if result else "failed"))
    return result


def extract_commands(args, commands):
    # reset command
    if args.device_command not in commands:
        args.device_command = ''
    if args.query:
        parts = re.split('\s+('+'|'.join(commands)+')(?i)', args.query)
        log.debug("query parts are "+str(parts))
        args.query = parts[0]
        if(len(parts) > 1):
            args.device_command = parts[1].lower()
        if(len(parts) > 2):
            args.device_param = parts[2].lower()
    return args

def main(wf):
    # list of commands
    commands = ['on', 'off']
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
    parser.add_argument('--device-name', dest='device_name', default=None)
    parser.add_argument('--device-uid', dest='device_uid', default=None)
    parser.add_argument('--device-command', dest='device_command', default='')
    parser.add_argument('--device-param', dest='device_param', default='')
    # scene name, uid, command and any command params
    parser.add_argument('--scene-name', dest='scene_name', default=None)
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
    handle_switch_commands(api_key, args, commands)
    handle_scene_commands(api_key, args)

    # since this ia now sure to be a device/scene query, fix args if there is a device/scene command in there
    args = extract_commands(args, commands)
 
    # update query post extraction
    query = args.query

    ####################################################################
    # View/filter devices or scenes
    ####################################################################

    # retrieve cached devices and scenes
    devices = wf.stored_data('devices')
    scenes = wf.stored_data('scenes')

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
        switches = wf.filter(query, devices, key=search_key_for_switch, min_score=20)
        scenes = wf.filter(query, scenes, key=search_key_for_scene, min_score=20)

        # Loop through the returned switches and add an item for each to
        # the list of results for Alfred
        for switch in switches:
            wf.add_item(title=switch['label'],
                    subtitle='Turn '+switch['label']+' '+args.device_command,
                    arg='--device-name "'+switch['label']+'" --device-uid '+switch['deviceId']+' --device-command '+args.device_command,
                    autocomplete=switch['label'],
                    valid=args.device_command in commands,
                    icon=ICON_SWITCH)

        # Loop through the returned scenes and add an item for each to
        # the list of results for Alfred
        for scene in scenes:
            wf.add_item(title=scene['sceneName'],
                    subtitle='Run '+scene['sceneName'],
                    arg='--scene-name "'+scene['sceneName']+'" --scene-uid '+scene['sceneId'],
                    autocomplete=scene['sceneName'],
                    valid=True,
                    icon=ICON_COLOR)

        # Send the results to Alfred as XML
        wf.send_feedback()
    return 0


if __name__ == u"__main__":
    wf = Workflow(update_settings={
        'github_slug': 'schwark/alfred-smartthings-py',
        'version': __version__
    })
    log = wf.logger
    if wf.update_available:
        # Add a notification to top of Script Filter results
        wf.add_item('New version available',
                'Action this item to install the update',
                autocomplete='workflow:update',
                icon=ICON_INFO)
    sys.exit(wf.run(main))
    