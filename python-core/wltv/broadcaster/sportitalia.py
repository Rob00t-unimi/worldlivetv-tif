# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://sportitalia.it/"

CHANNELS = {
    "sihd": "Sportitalia HD",
    "calcio": "Solo Calcio",
    "primaveratv": "Primavera TV",
    "laziostyle": "Lazio Style"
}

def play(search):
    res = BroadcasterResult()

    headers = utils.getBrowserHeaders(host=HOST)
    chId = CHANNELS[search]

    data = requests.get(HOST, headers=headers).text

    pattern = fr'<a[^>]+href="([^"]+)"[^>]*?>\s*<img[^>]+alt="{chId}"[^>]*?>\s*</a>'
    urlPage = scrapers.findSingleMatch(data, pattern)

    if urlPage:
        data = requests.get(urlPage, headers=headers).text
        pattern = r'file:\s*"([^"]+)"'
        url = scrapers.findSingleMatch(data, pattern)
        if not url:
            pattern = r'STREAM_URL\s=\s*"([^"]+)"'
            url = scrapers.findSingleMatch(data, pattern)
    
    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res