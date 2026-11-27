# -*- coding: utf-8 -*-

import requests
from lib import scrapers, config, logger
from lib.broadcaster_result import BroadcasterResult

# plugin://plugin.video.wltvhelper/play/

HOST = "https://www.google.com"

mpd = False 


def play(search):
    res = BroadcasterResult()
    url = ""

    data = requests.get(f"{HOST}/{search}").text
    url  = scrapers.findSingleMatch(data, r"regularexpression")

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
