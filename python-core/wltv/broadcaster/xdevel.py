# -*- coding: utf-8 -*-

import requests, json
from time import time
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://play.xdevel.com"
# plugin://plugin.video.wltvhelper/play/xdevel/xxxxx
# plugin://plugin.video.wltvhelper/play/xdevel/api$aHR0cHM6Ly93d3cudGVsZXBlZ2Fzby5pdA==   # https://www.telepegaso.it


def play(search):
    res = BroadcasterResult()
    url = ""

    splitted = search.split('$')
    if len(splitted) > 1:
        return playApi(splitted[1])

    headers = utils.getBrowserHeaders()
    data = requests.get(f"{HOST}/{search}", headers=headers).text
    jsonStr = scrapers.findSingleMatch(data, r"PLAYER_CONFIG\s+=\s+(\{.+?\});\s+")
    jsonData = json.loads(jsonStr)

    station = jsonData["defaultStation"]
    channel = jsonData["stations"][station]["channel"]
    
    url = channel["sources"][0]["source"]

    # useWAS key is not always present in the "channel" dictionary
    useWas = False
    try:
        useWas = channel["useWAS"]
    except KeyError:
        pass

    if useWas:
        headers["Referer"] = f"{HOST}/{search}/{station}"
        jsonData = requests.get(f"{HOST}/was", headers=headers).json()
        was = jsonData["was"]

        headers = utils.getBrowserHeaders(host=HOST)

        url = f"{url}?wmsAuthSign={was}"

    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res


def playApi(search):
    res = BroadcasterResult()
    url = ""

    API = "https://share.xdevel.com/api"
    search = utils.fromBase64(search)

    headers = utils.getBrowserHeaders()
    data = requests.get(f"{search}", headers=headers).text
    chKey = scrapers.findSingleMatch(data, r"xdevel.*?key=([^&]+)")
    
    #headers["Referer"] = search
    #https://share.xdevel.com/api/?platform=streamsolution&get=player&key=5d04168ba6d070135bcd35003ca848c4&ver=5
    
    dt = int(time() * 1000)

    jsonUrl = f"{API}/?platform=streamsolution&get=playersettings&key={chKey}&rdm={dt}&preview=0"
    headers["Referer"] = f"{API}/?platform=streamsolution&get=player&key={chKey}&ver=5"
    jsonData = requests.get(jsonUrl, headers=headers).json()
    key = jsonData["channels"]["0"]["key"]

    jsonUrl = f"{API}/?platform=streamsolution&get=streamingsettings&key={key}&rdm={dt}"
    headers["Referer"] = f"{API}/?platform=streamsolution&get=player&key={chKey}&ver=5"
    jsonData = requests.get(jsonUrl, headers=headers).json()
    
    urls = jsonData["params"]["playurls"]
    hlsUrl = urls["m3u8"][0]
    mpdUrl = urls["dash"][0]
    url = hlsUrl
    
    res.Url = url
    res.UseInputStreamAdaptive = False

    return res

