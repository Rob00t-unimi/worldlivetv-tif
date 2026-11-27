# -*- coding: utf-8 -*-

import requests, json
from lib import scrapers, logger, utils
from lib.broadcaster_result import BroadcasterResult


def play(search):
    res = BroadcasterResult()

    channels = {"SMRTV": 0, "SMRTVS": 1}
    url = ""

    if search in channels:
        requrl = f"https://catchup.acdsolutions.it/jstag/videoplayerLiveFluid/TV?ch={channels[search]}&eID=livePlayerPageElement&vID=666666666&autoPlay=true"
        data = requests.get(requrl, headers=utils.getBrowserHeaders()).text
        url = scrapers.findSingleMatch(data, r'src\s?=\s?"([^"]+)')

    if url:
        res.Url = url

    return res
