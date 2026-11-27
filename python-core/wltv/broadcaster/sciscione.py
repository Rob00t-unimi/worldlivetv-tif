#
# -*- coding: utf-8 -*-
#

import requests

from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

# Premio link 
# /premio/search

def play(search):
    HOST = "https://www.grupposciscione.it"
    res = BroadcasterResult()
    url = ""

    pageUrl = f"{HOST}/{search}/"
    data = requests.get(pageUrl, headers=utils.getBrowserHeaders()).text
    url = scrapers.findSingleMatch(data, r"data-video-source=\"\[{source:'(.*?)'")

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
