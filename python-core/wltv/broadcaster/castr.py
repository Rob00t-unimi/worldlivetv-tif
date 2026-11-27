# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils
from lib.broadcaster_result import BroadcasterResult


def play(search):
    HOST = "https://player.castr.com"
    res = BroadcasterResult()
    url = ""
    headers = utils.getBrowserHeaders(host=HOST)

    pageUrl = f"{HOST}/{search}"
    data = requests.get(pageUrl, headers=headers).text

    url = scrapers.findSingleMatch(data, r'window\.__streamUrl\s*=\s*"([^"]+)"')

    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res
