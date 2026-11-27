# -*- coding: utf-8 -*-

import requests, uuid
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult
from urllib.parse import urlencode

HOST = "https://www.radiosaiuz.it"

def play(search):
    res = BroadcasterResult()
    url = ""

    headers = utils.getBrowserHeaders()
    referer = f"{HOST}/canali-tv-1.html"
    headers["Referer"] = referer

    dataUrl = f"{HOST}/{search}.html"
    data = requests.get(dataUrl, headers = utils.getBrowserHeaders()).text
    dataUrl = scrapers.findSingleMatch(data, r'<iframe.*?src="([^"]+)"')

    headers["Referer"] = HOST

    data = requests.get(dataUrl, headers = utils.getBrowserHeaders()).text
    url = scrapers.findSingleMatch(data, r'<video\b[^>]*>[\s\S]*?<source[^>]*\bsrc="([^"]+)"[^>]*>[\s\S]*?<\/video>')

    baseUrl = scrapers.findSingleMatch(url, r'^(http[s]?://[^/]+)')

    if "/stream/play.m3u8" in data:
        url = f"{baseUrl}/stream/play.m3u8";

    headers["Referer"] = f'{HOST}/'
    headers["Origin"] = baseUrl

    if url:
        res.Url = url
        res.StreamHeaders = headers
        res.ManifestHeaders = headers

    return res


# def play_old(search):
#     res = BroadcasterResult()
#     url = ""

#     url = GetStaticUrlFromPage(search)

#     if not url:
#         clientId = str(uuid.uuid1())
#         PARENTID = 476482
        
#         querystringParameters = {
#             "X-Emby-Client":"Emby Web",
#             "X-Emby-Device-Name":"Chrome Windows",
#             "X-Emby-Device-Id":clientId,
#             "X-Emby-Client-Version":"4.8.0.0",
#             "X-Emby-Language":"it",
#         }

#         data = {"Username": "ospite"}
#         querystring = urlencode(querystringParameters)
#         dataUrl = f"{HOST}/emby/Users/authenticatebyname?{querystring}"
#         jsonData = requests.post(dataUrl, headers = utils.getBrowserHeaders(), data = data).json()

#         tk = jsonData.get("AccessToken", "")
#         userId = jsonData.get("SessionInfo", {}).get("UserId", "")
        
#         querystringParameters["X-Emby-Token"] = tk
#         querystringParameters["UserId"] = userId
        
#         chId1 = search
#         chId2 = ""

#         if not chId1.isnumeric():
#             chId1 = GetChId(search, querystringParameters.copy())
#             chId2 = GetChId(search, querystringParameters.copy(), PARENTID)

#         querystringParametersItem = querystringParameters.copy()
#         querystringParametersItem["StartTimeTicks"] = 0
#         querystringParametersItem["IsPlayback"] = "true"
#         querystringParametersItem["AutoOpenLiveStream"] = "true"
#         querystringParametersItem["MaxStreamingBitrate"] = 5985000
#         querystringParametersItem["reqformat"] = "json"

#         querystring = urlencode(querystringParametersItem)
        
#         url1 = GetUrl(chId1, querystring)
#         url2 = GetUrl(chId2, querystring)
        
#         if url1:
#             url = url1
#         else:
#             url = url2

#     if url:
#         res.Url = url
#         res.UseInputStreamAdaptive = False

#     return res

# def GetChId(search, querystringParameters, PARENTID=None):
#         chId = ""

#         userId = querystringParameters["UserId"]
#         querystringParameters.pop("UserId")

#         querystringParametersLC = querystringParameters
#         querystringParametersLC["SortBy"] = "DefaultChannelOrder"
#         querystringParametersLC["SortOrder"] = "Ascending"
#         querystringParametersLC["IncludeItemTypes"] = "TvChannel"
#         querystringParametersLC["Recursive"] = "true"
#         querystringParametersLC["Fields"] = "BasicSyncInfo,CanDelete,Container,ProgramPrimaryImageAspectRatio"
#         querystringParametersLC["StartIndex"] = 0
#         querystringParametersLC["EnableImageTypes"] = "Primary,Backdrop,Thumb"
#         querystringParametersLC["ImageTypeLimit"] = 1
#         querystringParametersLC["Limit"] = 100

#         if PARENTID:
#             querystringParametersLC.pop("IncludeItemTypes")
#             querystringParametersLC.pop("Recursive")
#             querystringParametersLC["ParentId"] = PARENTID
    
#         querystring = urlencode(querystringParametersLC)

#         dataUrl = f"{HOST}/emby/Users/{userId}/Items?{querystring}"
#         jsonData = requests.get(dataUrl, headers = utils.getBrowserHeaders()).json()

#         items = jsonData.get("Items", [])
#         jsonData = None
#         item = None

#         for i in items:
#             name = i["Name"]
#             if PARENTID and len(name.split("-")) > 1 and name.split("-")[1].strip().replace(" ", "-").casefold() == search.casefold():
#                 item = i
#                 break
#             elif name.strip().replace(" ", "-").casefold() == search.casefold():
#                 item = i
#                 break
        
#         if item:
#             chId = item.get("Id", "")

#         return chId

# def GetUrl(chId, querystring):
#     url = ""
#     if chId:
#         dataUrl = f"{HOST}/emby/Items/{chId}/PlaybackInfo?{querystring}"
#         jsonData = requests.get(dataUrl, headers = utils.getBrowserHeaders()).json()

#         ms = jsonData.get("MediaSources", [])
#         if ms:
#             url = ms[0].get("Path", "")

#     return url

# def GetStaticUrlFromPage(channelName):
    # url = ""
    # dataUrl = f"{SAIUZ_HOST}/{channelName}.html"
    # data = requests.get(dataUrl, headers = utils.getBrowserHeaders()).text
    # url = scrapers.findSingleMatch(data, r'<source\r*?\s*src="([^"]+)')

    # return url