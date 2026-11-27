# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

# plugin://plugin.video.wltvhelper/play/telelombardia/topcalcio24

HOST = "https://telelombardia.video"


def play(search):
    res = BroadcasterResult()
    url = ""

    headers = utils.getBrowserHeaders()
    req = requests.Session()
    req.get(HOST, headers=headers)

    videoIndex = f"{HOST}/video/index"
    data = req.get(videoIndex, headers=headers).text
    token = scrapers.findSingleMatch(data, r"name=\"csrf-token\"\scontent=\"([^\"]+)\"")
    data = None

    formData = {"rel": 0, "_csrf": token}
    jsonData = req.post(f"{HOST}/list/get-evidence-list", headers=headers, data=formData).json()

    channels = jsonData.get("evidenceVideoList", [])
    jsonData = None
    channel = next( iter( filter( lambda c: (c.get("channel_name", "").replace(" ", "").lower() == search.lower()), channels ) ) )
    chId = channel.get("files_id", 0);

    headers["Referer"] = videoIndex

    data = req.get(f"{HOST}/video/viewlivestreaming?rel={chId}&cntr=0", headers=headers).text
    
    url = scrapers.findSingleMatch(data, r"videoPlayerBab.*?src=\"(.*?)\"").strip()
    
    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
