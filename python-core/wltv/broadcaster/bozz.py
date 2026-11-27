# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST1 = "https://ssh101.com/"
HOST2 = "https://v2.ssh101.com/"

#use: plugin://plugin.video.wltvhelper/play/bozz/emmetv89

def play(search):
    res = BroadcasterResult()
    url = ""

    url = GetUrl(HOST1, search)

    if not url:
        url = GetUrl(HOST2, search)

    if url:
        res.Url = url

    return res

def GetUrl(host, search):
    pageUrl = f"{host}securelive/index.php?id={search}"
    data = requests.get(pageUrl).text
    url = scrapers.findSingleMatch(data, r'source\s?src="([^"]+)')
    if not url:
        url = scrapers.findSingleMatch(data, r'x-mpegurl",\ssrc:\s"([^"]+)')

    if CheckUrl(url, host):
        return f"{url}|referer{host}"
    return ""

def CheckUrl(url, referer):
    code = -1
    header = utils.getBrowserHeaders(host=referer);

    try:
        code = requests.get(url).status_code
    except :
        pass
    return code == 200
