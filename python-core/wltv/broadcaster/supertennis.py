# -*- coding: utf-8 -*-

import requests
from lib import scrapers, config, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://supertennis.tv/"

# headers = {
#     "User-Agent": utils.USER_AGENT,
#     "Referer": HOST,
#     "Sec-Fetch-Site": "cross-site",
#     "Sec-Fetch-Mode": "navigate",
#     "Sec-Fetch-Dest": "iframe",
# }

headers = utils.getBrowserHeaders(host=HOST)

def play(search):
    res = BroadcasterResult()

    url = ""

    data = requests.get(f"{HOST}live-streaming").text
    jsSuffix = scrapers.findSingleMatch(data, r'live-streaming([^"]+)')

    data = requests.get(f"{HOST}Areas/Supertennis/Scripts/live-streaming{jsSuffix}").text
    url = scrapers.findSingleMatch(data, r'manifestUrl\s*=\s*"([^"]+)"')

    if url:
        res.UserAgent = True
        res.Url = url

    return res
