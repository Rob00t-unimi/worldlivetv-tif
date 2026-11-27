# -*- coding: utf-8 -*-

import requests
from lib import utils, logger, const
from lib.broadcaster_result import BroadcasterResult
from urllib.parse import quote

host = "https://adtv.ae/api/biz/live/playinfo?channelExternalId={}"

headers = {
    "User-Agent": const.USER_AGENT,
}


def play(search):
    res = BroadcasterResult()
    url = ""

    _json = requests.get(host.format(quote(search)), headers=headers).json()
    url = _json.get("response", {}).get("playingUrl", "")

    if url:
        res.Url = url

    return res
