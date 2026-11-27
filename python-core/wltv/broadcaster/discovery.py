# -*- coding: utf-8 -*-

import requests, uuid, json
from lib import config, utils, logger, const, wltvcache
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.discoveryplus.com"
deviceId = uuid.uuid4().hex
dplusVer = "2.67.0"
cacheKey = "discoverychannels"

channelConfigs = { 
    "Nove": { "id": 3,  "code": "nove", "host": "nove.tv" },
    "RealTime": { "id": 2,  "code": "realtime", "host": "realtime.it" },
    "Discovery": { "id": 12,  "code": "discoverychannelit", "host": "discovery.it" },
    "DMAX": { "id": 4,  "code": "dmaxit", "host": "dmax.it" },
    "Giallo": { "id": 27,  "code": "giallo", "host": "giallotv.it" },
    "Turbo":{ "id": 11,  "code": "motortrend", "host": "discoveryturbo.it" },
    "HGTV": { "id": 13,  "code": "hgtvit", "host": "homegardentv.it" },
    "FoodNetwork": { "id": 6,  "code": "foodnetwork", "host": "foodnetwork.it" },
    "K2": { "id": 24,  "code": "k2", "host": "k2tv.it" },
    "Frisbee": { "id": 26,  "code": "frisbee", "host": "frisbeetv.it" }
 }


def play(search):
    return playFromSpecific(search)


def playFromDPlus(search):
    res = BroadcasterResult()
    chId = ""
    
    headers = utils.getBrowserHeaders(host=HOST)

    headers["Accept"] = "*/*"
    headers["x-disco-client"] = f"WEB:UNKNOWN:dplus_us:{dplusVer}"
    headers["x-disco-params"] = "bid=dplus,hn=www.discoveryplus.com,hth=it"

    discovery = wltvcache.get_or_set_string(cacheKey)
    if not discovery:
        discovery = GetChannels(headers)
        wltvcache.get_or_set_string(cacheKey, json.dumps(discovery), 10*60)
    else:
        discovery = json.loads(discovery)

    cookies = discovery["cookies"]
    baseApiUrl = discovery["baseApiUrl"]
    channels = discovery["channels"]
    discovery = None

    for key in channels:
        if (key.get("attributes", {}).get("hasLiveStream", "") == True
            and "Free" in key.get("attributes", {}).get("packages", [])
            and search == key["attributes"]["channelCode"]):
            chId = key["id"]
            break

    channels = None

    if chId:
        postJsonData = f'{{ "channelId": "{chId}", "deviceInfo": {{ "adBlocker": false, "drmSupported": true }}, "wisteriaProperties": {{ "siteId": "dplus_it", "platform": "desktop" }} }}'

        headers["x-disco-params"] = "realm=dplay,siteLookupKey=dplus_it,bid=dplus,hn=www.discoveryplus.com,hth=it,uat=false"
        headers["Content-Type"] = "application/json"
        
        jsonData = requests.post(f"{baseApiUrl}/playback/v3/channelPlaybackInfo", headers=headers, cookies=cookies, data=postJsonData).json()

        data = jsonData.get("data", {}).get("attributes", {}).get("streaming", {})[0]
        jsonData = None

        url = data["url"]

        if url:
            headers = utils.getBrowserHeaders(host=HOST)
            res.Url = url
            res.UserAgent = True
            res.StreamHeaders = headers
            
            if data["protection"]["drmEnabled"] == True:
                drmToken = data["protection"]["drmToken"]
                licenseUrl = data["protection"]["schemes"]["widevine"]["licenseUrl"]

                licenseConfig = { 
                    'license_server_url': licenseUrl,
                    'headers': utils.dict2querystring(headers),
                    'post_data': 'R{SSM}',
                    'response_data': 'R'
                }
                res.LicenseKey = '|'.join(licenseConfig.values())
                #res.LicenseType  = "com.microsoft.playready"

    return res

def playFromSpecific(search):
    res = BroadcasterResult()
    mpd = config.getSetting("discoverympd")

    ch = channelConfigs[search]
    headers = utils.getBrowserHeaders(host=f'https://{ch["host"]}')
    
    baseApiUrl = "https://public.aurora.enhanced.live"
    
    # Forza endpoint e realm per K2 e Frisbee
    if search.lower() in ["k2", "frisbee"]:
        logger.dbg(True)
        channelId = ch["id"]
        realm = "it"
    else:
        configUrl = f'{baseApiUrl}/site/configurations/?include=default&filter[environment]={ch["code"]}&v=2'
        jsonData = requests.get(configUrl, headers=headers).json()
        pl = jsonData["settings"]["site"]["simulcast"]

        baseApiUrl = pl["sonicEndpoint"]
        channelId = pl["channelId"]
        realm = pl["sonicRealm"]

    headers["X-Device-Info"] = "STONEJS/1 (Unknown/Unknown; Windows/NT 10.0; Unknown)"
    headers["X-disco-params"] = f"realm={realm}"
    headers["X-disco-client"] = "WEB:UNKNOWN:wbdatv:2.1.9"
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "*/*"

    jsonData = requests.get(f"{baseApiUrl}/token?realm={realm}", headers=headers).json()
    tk = jsonData["data"]["attributes"]["token"]

    headers["Authorization"] = f"Bearer {tk}"
    
    postJsonData = f'{{"deviceInfo":{{"adBlocker":false,"drmSupported":true,"hdrCapabilities":["SDR"],"hwDecodingCapabilities":[],"soundCapabilities":["STEREO"]}},"wisteriaProperties":{{"device":{{"browser":{{"name":"chrome","version":"{const.BROWSER_VERSION}"}},"type":"desktop"}},"platform":"desktop"}},"channelId":"{channelId}"}}'
    jsonData = requests.post(f"{baseApiUrl}/playback/v3/channelPlaybackInfo", headers=headers, data=postJsonData).json()

    streamings = jsonData.get("data", {}).get("attributes", {}).get("streaming", [])
    
    order = ["dash", "hls"] if mpd else ["hls", "dash"]
    url = next((s.get("url") for t in order for s in streamings if s.get('type') == t), "")

    if url:
        headers = utils.getBrowserHeaders(host=HOST)
        res.Url = url
        res.UserAgent = True
        res.StreamHeaders = headers
        res.Delay = config.getSetting("discoverydelay")

    return res

def GetChannels(headers):
    infoUrl = "https://global-prod.disco-api.com/bootstrapInfo"
   
    jsonData = requests.get(infoUrl, headers=headers).json()
    baseApiUrl = jsonData.get("data", {}).get("attributes", {}).get("baseApiUrl", "")

    #get token
    headers["x-device-info"]  = f"dplus_us/{dplusVer} (desktop/desktop; Windows/NT 10.0; {deviceId})"
    headers["x-disco-params"] = "realm=dplay,bid=dplus,hn=www.discoveryplus.com,hth=it,features=ar"

    token = requests.get(f"{baseApiUrl}/token?deviceId={deviceId}&realm=dplay&shortlived=true", headers=headers).json()["data"]["attributes"]["token"]
    cookies = { "st": token }

    channels = requests.get(f"{baseApiUrl}/cms/routes/home?include=default&decorators=playbackAllowed", headers=headers, cookies=cookies).json()["included"]
    channels = list(filter(lambda x: x.get("type", "") == "channel", channels))

    for chs in channels:
        chs.pop("relationships", None)
        chs.get("attributes", {}).pop("contentDescriptors", None)
        chs.get("attributes", {}).pop("contentRatings", None)
        chs.get("attributes", {}).pop("customAttributes", None)
        chs.get("attributes", {}).pop("longDescription", None)
        #chs.get("attributes", {}).pop("packages", None)
    
    discovery = {
       "baseApiUrl": baseApiUrl,
       "cookies": cookies,
       "channels": channels
    }

    return discovery