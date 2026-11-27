# -*- coding: utf-8 -*-

import requests, json
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult


def GetBroadcasterResult(urlInfo, headers):
    res = BroadcasterResult()
    url = ""

    data = requests.get(urlInfo, headers=headers).text
    requestHost = scrapers.findSingleMatch(data, r"requestHost:\s*'([^']+)'")
    jsonData = scrapers.findSingleMatch(data, r'contentInfo:\s*({[\s\S]*?}),(?=\s*skinId)')
    jsonData = json.loads(jsonData)
    
    liveHost = jsonData.get("host", "")
    liveSourceID = jsonData.get("liveSourceID", "")
    contentID = jsonData.get("contentID", "")

    url = f"https://{liveHost}/live/{liveSourceID}/{contentID}/playlist.m3u8"
    headers = utils.getBrowserHeaders(host=requestHost)

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = True
        res.StreamHeaders = headers

    return res