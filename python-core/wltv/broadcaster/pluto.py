# -*- coding: utf-8 -*-

import uuid, requests, sys
from datetime import datetime, timedelta
from lib import logger, scrapers, utils
from lib.broadcaster_result import BroadcasterResult

from urllib.parse import unquote

HOST_API = "https://api.pluto.tv"
UUID = uuid.uuid1().hex
DEVICEID = uuid.uuid1()


def play(search):
    res = BroadcasterResult()

    url = ""

    search = unquote(search)
    headers = utils.getBrowserHeaders()

    channelsUrl = f"{HOST_API}/v2/channels.json?deviceId={UUID}"

    ids = {
        ch.get("slug"): ch.get("_id", "")
        for ch in requests.get(channelsUrl, headers = headers).json()
    }
    chId = ids.get(search)

    data = requests.get(f"https://pluto.tv/live-tv/{chId}", headers = headers).text
    appVersion = scrapers.findSingleMatch(data, r'name="app_version" content="([^"]+)')
    data = None

    clientTime = datetime.utcnow()

    lastAppLaunchDate = clientTime - timedelta(minutes=20)
    clientTimeISO = clientTime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    lastAppLaunchDateISO = lastAppLaunchDate.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    bootPlutoParams = {
        "appName": "web",
        "appVersion": appVersion,
        "deviceVersion": "138.0.0",
        "deviceModel": "web",
        "deviceMake": "chrome",
        "deviceType": "web",
        "clientID": DEVICEID,
        "clientModelNumber": "1.0.0",
        "channelSlug": chId,
        "serverSideAds": "false",
        "drmCapabilities": "widevine%3AL3",
        "blockingMode": "",
        "notificationVersion": "1",
        "appLaunchCount": "2",
        "lastAppLaunchDate": lastAppLaunchDateISO,
        "clientTime": clientTimeISO
    }

    qs = utils.dict2querystring(bootPlutoParams)

    jsonData = requests.get(f"https://boot.pluto.tv/v4/start?{qs}", headers = headers).json()
    
    serverUrl = jsonData.get("servers", "").get("stitcher", "")
    pathUrl = jsonData.get("EPG", [])[0].get("stitched", "").get("paths", [])[0].get("path", "")

    stitcherParams = jsonData.get("stitcherParams", "")
    sessionToken = jsonData.get("sessionToken", "")

    if serverUrl and pathUrl and stitcherParams:
        url = f"{serverUrl}/v2{pathUrl}?{stitcherParams}&jwt={sessionToken}&masterJWTPassthrough=true" #"&gdpr=1&includeExtendedEvents=true&eventVOD=false"

    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res
