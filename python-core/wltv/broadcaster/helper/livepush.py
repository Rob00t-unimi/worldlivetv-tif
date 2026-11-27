# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult


def GetLivepush(videoId):
    res = BroadcasterResult()
    url = ""

    HOST = "https://livepush.io/"
    API = f"https://watch-api.livepush.io"
    jsonData = requests.get(f"{API}/v1/playback/{videoId}").json()
    
    url = jsonData.get("hls_url", "")

    if url:
        res.StreamHeaders = utils.getBrowserHeaders(host=HOST)
        res.Url = url

    return res
