# -*- coding: utf-8 -*-

import requests
from .helper import researcher as rs
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.antennasud.com"

CHANNELS = {
    "as": f"{HOST}/streaming",
    "92": f"{HOST}/streaming-92",
    "sport": f"{HOST}/streaming-sport",
    "sport2": f"{HOST}/streaming-sport-2",
    "sport3": f"{HOST}/streaming-as-sport-3",
    "sport4": f"{HOST}/streaming-as-sport-4",
    "sport5": f"{HOST}/streaming-as-sport-5",
    "tr": "https://www.teleregionecolor.com/teleregione-live-stream"
}

def play(search):
    res = BroadcasterResult()

    headers = utils.getBrowserHeaders(host=HOST)
    chUrl = CHANNELS[search]
    #logger.dbg(True)
    data = requests.get(chUrl, headers=headers, verify=False).text
    streamUrl = url = scrapers.findSingleMatch(data, r'<div.*?<iframe.*?src="([^"]+)')
    data = requests.get(streamUrl, headers=headers, verify=False).text
    streamUrl = rs.GetLink(data)

    if streamUrl:
        res.Url = streamUrl
        res.StreamHeaders = headers

    return res
