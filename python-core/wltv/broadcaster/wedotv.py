# -*- coding: utf-8 -*-

import requests, datetime
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.wedotv.com"

#use: plugin://plugin.video.wltvhelper/play/wedotv/5

def play(search):
    res = BroadcasterResult()
    url = ""

    url = GetUrl(HOST, search)

    if url:
        res.Url = url

    return res

def GetUrl(host, search):
    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    epgUrl = f"{host}/api/getEpg.php?offset=0&limit=100&date={dt}&genre=all"

    headers = utils.getBrowserHeaders()
    headers["Referer"] = f"{host}/it-it/channels/"
    headers["Cookie"] = "language=it; country=it"

    jsonEpg = requests.get(epgUrl, headers = headers).json()

    url = next((channel.get("hls", "") for channel in jsonEpg.get("channels", {}) if channel.get("id", "") == search), "")

    return url
