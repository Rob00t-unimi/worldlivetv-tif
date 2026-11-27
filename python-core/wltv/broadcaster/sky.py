# -*- coding: utf-8 -*-

import requests
from lib import utils
from lib.broadcaster_result import BroadcasterResult


def play(search):
    res = BroadcasterResult()

    channels = {"Sky TG24": 1, "Cielo": 2, "TV8": 7, "Sport24": 4}

    url = ""
    if search in channels:
        requrl = f"https://video.sky.it/api/v1/getLivestream?id={channels[search]}&isMobile=false"
        url = requests.get(requrl, utils.getBrowserHeaders()).json()["streaming_url"]

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
