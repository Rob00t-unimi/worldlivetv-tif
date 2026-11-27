# -*- coding: utf-8 -*-

import requests, json
import uuid
from lib import utils, scrapers
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.legaseriea.it"

def play(search):
    res = BroadcasterResult()
    headers = utils.getBrowserHeaders(host=HOST)
    
    siteUrl = f"{HOST}/radiotv"
    data = requests.get(siteUrl, headers=headers).text
    settingsBaseUrl = scrapers.findSingleMatch(data, r'DIVA_VIDEO_PLAYER_SETTINGS_BASE_URL[\\]*"\s*[:\\]+\s*[\\]*"([^"\\]+)')
    divaVideoWorkflow = scrapers.findSingleMatch(data, r'divaVideoWorkflow[\\]*"\s*[:\\]+\s*[\\]*"([^"\\]+)')
    videoId = scrapers.findSingleMatch(data, r'videoId[\\]*"\s*[:\\]+\s*[\\]*"([^"\\]+)')
    
    if settingsBaseUrl and divaVideoWorkflow and videoId:
        settingsUrl = f"{settingsBaseUrl}/{divaVideoWorkflow}/html5"
        settingsResp = requests.get(settingsUrl, headers=headers)
        settingsData = json.loads(settingsResp.content.decode('utf-8-sig'))
        videoDataPath = settingsData.get("videoData", {}).get("videoDataPath", "")
        entitlementUrl = settingsData.get("entitlementCheck", {}).get("entitlementUrl", "")
        
        configUrl = videoDataPath.replace("{v.id}", videoId)
        configData = requests.get(configUrl, headers=headers).json()
        
        sources = configData.get("sources", [])
        dashSource = next((s for s in sources if s.get("format") == "DASH" and s.get("name") == "Desktop-DASH"), None)
        
        if dashSource and entitlementUrl:
            sessionId = str(uuid.uuid4())
            playbackSessionId = str(uuid.uuid4()).upper()
            
            payload = {
                "Type": 1,
                "VideoId": videoId,
                "VideoSource": dashSource["uri"],
                "VideoKind": "live",
                "AssetState": "2",
                "PlayerType": "HTML5",
                "VideoSourceFormat": "DASH",
                "VideoSourceName": dashSource["name"],
                "DRMType": "",
                "AuthType": "Open",
                "SessionId": sessionId,
                "PlaybackSessionId": playbackSessionId,
                "Other": f"{sessionId}|web_browser",
                "User": ""
            }
            
            data = requests.post(entitlementUrl, headers=headers, json=payload).json()
            url = data.get("ContentUrl")
            
            if url:
                res.Url = url
                res.StreamHeaders = headers
    
    return res
