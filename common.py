from workflow import web
import json


def qnotify(title, text):
    print(text)

def error(text):
    print(text)
    exit(0)

def get_device(wf, device_uid):
    devices = wf.stored_data('devices')
    return next((x for x in devices if device_uid == x['deviceId']), None)

def get_scene(wf, scene_uid):
    scenes = wf.stored_data('scenes')
    return next((x for x in scenes if scene_uid == x['sceneId']), None)

def st_api(wf, api_key, url, params=None, method='GET', data=None):
    url = 'https://api.smartthings.com/v1/'+url
    headers = {'Authorization':'Bearer '+api_key,'Accept':"application/json"}
    r = None

    if('GET' == method):
        r = web.get(url, params, headers)
    else:
        headers['Content-type'] = "application/json"
        if data and isinstance(data, dict):
            data = json.dumps(data)
        wf.logger.debug("posting with data "+(data if data else ''))
        r = web.post(url, params, data, headers)

    wf.logger.debug("st_api: url:"+url+", method: "+method+",  headers: "+str(headers)+", params: "+str(params)+", data: "+str(data))
    # throw an error if request failed
    # Workflow will catch this and show it to the user
    r.raise_for_status()

    # Parse the JSON returned by pinboard and extract the posts
    result = r.json()
    #log.debug(str(result))
    return result    

def get_stored_data(wf, name):
    data = {}
    try:
        data = wf.stored_data(name)
    except ValueError:
        pass
    return data

