#
# -*- coding: utf-8 -*-
#

import requests

from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

# Premio link 
# /premio/search

def play(search):
    HOST = "https://player.premio.link"
    res = BroadcasterResult()
    url = ""

    pageUrl = f"{HOST}/watch/?l={search}"
    data = requests.get(pageUrl, headers=utils.getBrowserHeaders(host=HOST)).text

    url = scrapers.findSingleMatch(data, r'<source\ssrc="(.*?)"')

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
