#
# -*- coding: utf-8 -*-
#

import requests

from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

# Vimeo "events"
# /vimeo/e$id

# Vimeo "live events"
# /vimeo/l$id

# Vimeo "videos"
# /vimeo/v$id

HOST = "https://vimeo.com"

def play(search):
    res = BroadcasterResult()
    url = ""

    sSplit = search.split("$")
    itemType = sSplit[0].lower()
    id = sSplit[1]
    videoId = ""

    if itemType == "e":
        videoId = getVideoIdFromEmbed(HOST, id)
    elif itemType == 'l':
        url = getUrlFromStatus(HOST, id)
    else:
        videoId = id

    if videoId:
        url = f"plugin://plugin.video.vimeo/play/?video_id={videoId}"

    if url:
        res.Url = url
        res.StreamHeaders = utils.getBrowserHeaders(HOST)

    return res

def getVideoIdFromEmbed(baseUrl, eventId) -> str:
    videoId = ""
    pageUrl = f"{baseUrl}/event/{eventId}/embed/"

    data = requests.get(pageUrl).text
    if data:
        videoId = scrapers.findSingleMatch(data, r'data-clip-id="([^"]+)"')
        data = None

    return videoId

def getUrlFromStatus(baseUrl: str, eventId: int) -> str:
    url = ""
    pageUrl = f"{baseUrl}/live_event/{eventId}/status"

    config = requests.get(pageUrl).json().get("next_live_clip", {}).get("config_no_autoplay", "")

    if config:
        hlsjs = requests.get(config).json() \
                        .get("request", {}) \
                        .get("files", {}) \
                        .get("hls", "")
        if hlsjs:
            default_cdn = hlsjs.get("fastly_live", "akamai_live")
            url = hlsjs.get("cdns", {}) \
                       .get(default_cdn, {}) \
                       .get("url")

    return url
