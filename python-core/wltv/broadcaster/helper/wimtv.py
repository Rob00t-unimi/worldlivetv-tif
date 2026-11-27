# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

TOKENHOST = "https://platform.wim.tv"


def GetWimFromUrl(HOST, chType="live"):
    headers = utils.getBrowserHeaders()
    data = requests.get(HOST, headers=headers).text

    return GetWimFromData(data, chType)

    #pageUrl = scrapers.findSingleMatch(data, r'<iframe.*?src="([^"]+)"')
    #chId = scrapers.findSingleMatch(pageUrl, r'=([^&]+)')

    # pageUrl = scrapers.findSingleMatch(data, r'<iframe.*?src=".*?wim.tv.*?\/([^"]+)"')
    # chId = utils.getGuid(pageUrl)

    # return GetWimUrlByChId(chId)


def GetWimFromData(data, chType="live"):
    pageUrl = scrapers.findSingleMatch(data, r'<iframe.*?src=".*?wim.tv.*?\/([^"]+)"')

    if pageUrl:
        chId = utils.getGuid(pageUrl)
    else:
        chId = scrapers.findSingleMatch(data, r'src=[^\?]+\?cast=([^\\]+)')

    return GetWimUrlByChId(chId, chType)


def GetWimUrlByChId(chId, chType="live"):
    res = BroadcasterResult()
    url = ""

    headers = utils.getBrowserHeaders()
    tokenUrl = f"{TOKENHOST}/wimtv-server/oauth/token"
    pageUrl = f"{TOKENHOST}/embed/?{chType}={chId}"
    chId = scrapers.findSingleMatch(pageUrl, r'=([^&]+)')

    headers["Referer"] = pageUrl
    headers["Authorization"] = "Basic d3d3Og=="
    
    argsData = { "grant_type": "client_credentials" }
    jsonData = requests.post(tokenUrl , headers=headers, data=argsData).json()
    token = jsonData["access_token"]

    jsonUrl = f"{TOKENHOST}/wimtv-server/api/public/{chType}/channel/{chId}/play"

    headers["Accept-Language"] = "it"
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    headers["X-Wimtv-timezone"] = "3600000"
    headers["Origin"] = TOKENHOST
    headers["Accept"] = "application/json"
    headers["X-Requested-With"] = "XMLHttpRequest"

    jsonData = requests.post(jsonUrl, headers=headers, json={}).json()

    url = jsonData["srcs"][0]["uniqueStreamer"]

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res