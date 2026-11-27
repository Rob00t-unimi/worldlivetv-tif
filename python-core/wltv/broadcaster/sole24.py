# -*- coding: utf-8 -*-

import requests, json
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult
from time import time


HOST = "https://stream24.ilsole24ore.com"


def play(search):
    res = BroadcasterResult()

    siteUrl = f"https://s24ore.it/flussotv"
        
    headers = utils.getBrowserHeaders()

    data = requests.get(siteUrl, headers = headers).text
    jsonData = scrapers.findSingleMatch(data, r'<script type="application/ld\+json">([^<]+)')
    jsonData = json.loads(jsonData)

    embedUrl = jsonData.get("video", {}).get("embedUrl", "")

    headers = utils.getBrowserHeaders(host=HOST)

    data = requests.get(embedUrl, headers = headers).text
    embedUrl = scrapers.findSingleMatch(data, r'<div class="videoFullscreenIframe[^"]*">\s*<iframe[^>]*src="([^"]+)"')

    data = requests.get(embedUrl, headers = headers).text

    videoId = scrapers.findSingleMatch(data, r'data-video-id="([^"]+)')
    account = scrapers.findSingleMatch(data, r'data-account="([^"]+)')
    player = scrapers.findSingleMatch(data, r'data-player="([^"]+)')

    data = requests.get(f"https://players.brightcove.net/{account}/{player}_default/index.min.js", headers = headers).text
    policyKey =  scrapers.findSingleMatch(data, r'policyKey:"([^"]+)')

    headers["Accept"] = f"application/json;pk={policyKey}"
    bcUrl = f"https://edge.api.brightcove.com/playback/v1/accounts/{account}/videos/{videoId}"
    data = requests.get(bcUrl, headers = headers).json()

    #url = next((source["src"] for source in data["sources"] if source.get("asset_id") == videoId), None)
    url = data["sources"][0]["src"]

    headers["Accept"] = "*/*"
    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res
