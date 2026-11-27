# -*- coding: utf-8 -*-
# youtube channel & video broadcaster

#example: 
    #   www.youtube.com/channel/UC3yM6JHZSBlU8crXIDHK-kQ/streams
    #   plugin://plugin.video.wltvhelper/play/yt/c/UC3yM6JHZSBlU8crXIDHK-kQ/milanow <== old multi live stream

    #   www.youtube.com/@QsvsTopCalcio24/streams (milanow)
    #   www.youtube.com/@QsvsTopCalcio24/streams/milanow <== write on m3u
    #   plugin://plugin.video.wltvhelper/play/yt/c/@QsvsTopCalcio24/milanow     <== multi live stream

    #   www.youtube.com/@QsvsTopCalcio24/streams (top calcio)
    #   www.youtube.com/@QsvsTopCalcio24/streams/top calcio <== write on m3u
    #   plugin://plugin.video.wltvhelper/play/yt/c/@QsvsTopCalcio24/top calcio  <== multi live stream

    #   www.youtube.com/@France24_en/live
    #   plugin://plugin.video.wltvhelper/play/yt/l/@France24_en  <== only single live stream (or default)

    #   plugin://plugin.video.wltvhelper/play/yt/v/TbhcfUPYKEU

import json
import requests
from urllib.parse import unquote
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.youtube.com"
CK = "SOCS=CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjQxMTI0LjA4X3AwGgJpdCACGgYIgJS5ugY"

def play(chtype:str,chId:str,chName:str):
    chName = unquote(chName)

    if chtype == "c":
        return playMultiLiveChannel(chId, chName)
    elif chtype == "l":
        return playSingleLiveChannel(chId)
    elif chtype == "v":
        return playVideo(chId)
    else:
        return playVideo(chId)

def playSingleLiveChannel(chId:str):
    videoId = ""

    headers = utils.getBrowserHeaders();
    headers["Cookie"] = CK

    data = requests.get(f"{HOST}/{chId}/live", headers=headers).text

    regex = r"window\['ytCommand'\].*?\"videoId\":\"([^\"]+)\""
    videoId = scrapers.findSingleMatch(data, regex)
    data = None

    return playVideo(videoId)


def playMultiLiveChannel(chId:str,chName:str):
    if chId.startswith('@'):
        videoInfoUrl = f"/{chId}"
    else:
        videoInfoUrl = f"/channel/{chId}"

    videoId = ""

    headers = utils.getBrowserHeaders();
    headers["Cookie"] = CK
  
    data = requests.get(f"{HOST}{videoInfoUrl}/streams", headers=headers).text 
    regex = r"ytInitialData\s?=\s?(.*?);<"
    jsonData = scrapers.findSingleMatch(data, regex)
    
    if not jsonData: #try with channelname
        videoInfoUrl = f"/c/{chId}/streams"
        data = requests.get(f"{HOST}{videoInfoUrl}", headers=headers).text 
        regex = r"ytInitialData\s?=\s?(.*?);<"
        jsonData = scrapers.findSingleMatch(data, regex)

    data = None

    jsonData = json.loads(jsonData)
    tabs = jsonData["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
    jsonData = None

    for tab in tabs:
        if tab.get("tabRenderer", {}).get("title", "") == "Live":
            liveContents = tab["tabRenderer"]["content"]["richGridRenderer"]["contents"]
            videoId = GetLiveVideoId(chName, liveContents)
            liveContents = None
        
        if videoId: 
            break
            
    tab = None
    tabs = None

    return playVideo(videoId)


def playVideo(videoId):
    res = BroadcasterResult()
    url = ""
    dashUrl = ""
    hlsUrl  = ""
    url = GetVideoUrl(videoId)

    # dashUrl, hlsUrl = GetVideoUrlDirect(videoId)

    # if dashUrl:
    #     url = dashUrl
    #     res.UseInputStreamAdaptive = True
    
    # if hlsUrl:
    #     url = hlsUrl
    #     res.UseInputStreamAdaptive = True

    # if not url:
    #     logger.info("Direct url NOT found, trying use plugin...")
    #     url = GetVideoUrl(videoId)
    # else:
    #     #res.UserAgent = True
    #     #url = utils.getUserAgentForLink(url)
    #     pass

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res


def GetLiveVideoId(chName, contents):
    items = []
    chName = chName.replace(" ", "").lower()

    for content in contents:
        try:
            videoRenderer = content["richItemRenderer"]["content"].get("videoRenderer", {})
            for thumb in videoRenderer.get("thumbnailOverlays", []):
                sk = next(iter(thumb))
                if thumb[sk].get("style", "") == "LIVE":
                    videoId = GetVideoIdFromVR(videoRenderer, chName, ["title"])
                    if videoId: 
                        return videoId
        except :
            pass

    return ""


def GetVideoIdFromVR(videoRenderer, chName, sections):
    videoId = ""
    for section in sections:
        dictTitle = videoRenderer.get(section, {})

        if dictTitle.get("runs", []):
            title = dictTitle.get("runs", [])[0].get("text", "")

            if chName == "" or chName == "0" or chName in title.replace(" ", "").lower():
                videoId = videoRenderer.get("videoId", "")
        if videoId:
            break

    return videoId


def GetVideoUrl(videoId):
    url = ""

    if videoId:
        url = f"plugin://plugin.video.youtube/play/?video_id={videoId}"
    else:
        logger.info("No YouTube streams found.")
        utils.MessageNotification(30204)

    return url


def GetVideoUrlDirect(videoId):
    dashUrl = ""
    hlsUrl  = ""

    if videoId:
        data = requests.get(f"{HOST}/watch?v={videoId}", headers=utils.getBrowserHeaders()).text
        regex = r"ytInitialPlayerResponse\s?=\s?(.*?);var"
        jsonData = scrapers.findSingleMatch(data, regex)
        data = None
        jsonData = json.loads(jsonData)
        streamingData = jsonData.get("streamingData", {})
        jsonData = None

        if streamingData:
            dashUrl = streamingData.get("dashManifestUrl", "")
            hlsUrl  = streamingData.get("hlsManifestUrl", "")

        if not dashUrl and not hlsUrl and streamingData:
            logger.info("No dashUrl and no hlsUrl found, try to get from 'formats'")
            hlsUrl = streamingData.get("formats", [])[-1].get("url", "")

    return dashUrl, hlsUrl
