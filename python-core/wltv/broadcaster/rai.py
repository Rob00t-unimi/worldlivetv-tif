# -*- coding: utf-8 -*-

import requests, xbmcgui, urllib, json
from lib import config, utils, logger, wltvcache
from lib.broadcaster_result import BroadcasterResult
from broadcaster import rainewsrg

HOST = "https://www.raiplay.it"
headers = utils.getBrowserHeaders()


def play(search):
    res = BroadcasterResult()
    res.Delay = config.getSetting("raidelay")
    url = ""
    title = ""

    hbbtv = True

    try:
        url, title = play_hbbtv(search)
    except:
        url, title = play_raiplay(search)
        
    if title:
        res.Title = title
    
    if url:
        result = getRealUrlAndLic(url)
        if result.get("drm", "") == "WIDEVINE":
            pass
        elif result.get("drm", "") == "PLAYREADY":
            #unsupported on windows so try to get hsl for now...
            result = getRealUrlAndLic(url, True)
        
        url = result.get("url", "")
        lic = result.get("lic", "")

        res.Url = url

        if lic:
            licenseUrl = lic.get("licenceUrl", "")
            parsed = urllib.parse.urlparse(licenseUrl)
            
            baseLicenseUrl = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            parameters = urllib.parse.parse_qs(parsed.query)

            tk = parameters.get("Authorization", [None])[0]

            headers = utils.getBrowserHeaders(host=HOST)
            headers["Accept"] = "*/*"
            
            res.StreamHeaders = headers

            headers["Accept"] = "application/octet-stream"
            headers["Content-Type"] = "application/octet-stream"
            headers["nv-authorizations"] = tk
            
            headers.pop("Accept-Encoding", None)
            headers.pop("Accept-Language", None)
            
            res.LicenseKey = f"{baseLicenseUrl}|{urllib.parse.urlencode(headers)}|R{{SSM}}|"

    return res


def getRealUrlAndLic(url, playReadyFound = False):
    lic = None
    drm = ""
    raimpd = config.getSetting("raimpd")
    raimpd = False

    fUA = "raiplayhbbtv"
    
    if playReadyFound or not raimpd:
        fUA = "raiplayappletv"

    url = f"{url}&output=63"
    url = f"{url}&forceUserAgent={fUA}"
    jsonConfig = requests.get(url, headers = headers).json()
    url = jsonConfig.get("video", [""])[0]
    licList = jsonConfig.get("licence_server_map", "").get("drmLicenseUrlValues", "")

    if licList:
        drm = "WIDEVINE"
        lic = next(filter(lambda l: l.get("drm", "") == drm, licList), None)
        
        if not lic:
            drm = "PLAYREADY"
            lic = next(filter(lambda l: l.get("drm", "") == drm, licList), None)

    return { "url": url, "lic": lic, "drm": drm }


def play_raiplay(search):
    url = ""
    title = ""
    
    reqUrl = "https://www.raiplay.it/dirette.json"

    jsonChannels = wltvcache.get_or_set_string("raiplaychannelsdirette")
    if not jsonChannels:
        jsonChannels = requests.get(reqUrl, headers = headers).json()["contents"]
    
        for channel in jsonChannels:
            channel.pop("rights_management", None)
            channel.pop("track_info", None)
            channel.pop("description", None)

            wltvcache.get_or_set_string("raiplaychannelsdirette", json.dumps(jsonChannels), 10*60)
    else:
        jsonChannels = json.loads(jsonChannels)

    service = next( iter( filter( lambda key: (key["channel"] == search), jsonChannels ) ) )
    if service:
        url = service["video"]["content_url"]

    return url, title


def play_hbbtv(search):
    url = ""
    title = ""
    
    items = getServices(search)

    service = list()
    if search == "Rai 3" and rainewsrg.isRai3NewsLive():
        rai3config = config.getSetting("rai3config")
        service = next( iter( filter( lambda c: (c["dvbTriplet"] == rai3config), items["Service"] ) ) )
    else:
        service = items["Service"][0]
    
    if service:
        url = service.get("url", "")
        title = service.get("name", "")

    return url, title


def getServices(search):
    reqUrl = "https://www.replaytvmhp.rai.it/hbbtv/launcher/RemoteControl/resources/srvConfig.json"

    services = wltvcache.get_or_set_string("raiplaychannelsservices")
    if not services:
        services = requests.get(reqUrl).json()["Configuration"]["Editors"]["Editor"]
    
        for service in services:
            service.pop("Service", None)
            service.pop("Analytics", None)
            service.pop("Digital", None)

            if service.get("Services", []):
                for s in service["Services"]:
                    if s.get("delivery", "") != "3":
                        s.pop("Service", None)

            wltvcache.get_or_set_string("raiplaychannelsservices", json.dumps(services), 10*60)
    else:
        services = json.loads(services)

    services = next( iter( filter( lambda c: (c["name"].casefold() == search.casefold()), services ) ) )
    services = next( iter( filter( lambda s: (s["delivery"] == "3"), services["Services"] ) ) )

    return services


def chooseRai3Region(): # <== used in settings to save the chosen region
    rai3config = "0.0.300"
    name = ""

    try:
        items = getServices("Rai 3")
        items = items["Service"]

        suffix = "Rai 3 TGR"
        lst = list()
        li = xbmcgui.ListItem("Default HD")
        li.setProperties({"dvbTriplet": rai3config})
        lst.append(li)

        items = sorted(items, key=lambda x: x['name'])
        for x in items:
            if x["name"].startswith(suffix):
                title = x["name"].replace(suffix, "").strip()
                li = xbmcgui.ListItem(title)
                li.setProperties({"dvbTriplet": x["dvbTriplet"]})
                lst.append(li)

        idx = xbmcgui.Dialog().select(config.getString(30183), lst)
        if idx > 0:
            rai3config = lst[idx].getProperty("dvbTriplet")
            name = lst[idx].getLabel()
        else: return
    except:
        utils.MessageBox(30184)

    config.setSetting("rai3config", rai3config)
    config.setSetting("rai3chosen", name)
