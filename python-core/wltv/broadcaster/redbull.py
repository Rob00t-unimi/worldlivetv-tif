# -*- coding: utf-8 -*-

import requests
from lib import utils
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.redbull.com"


def play(search):
    res = BroadcasterResult()

    url = ""
    tokenurl = "https://api.redbull.tv/v3/session?os_family=http"
    
    headers = utils.getBrowserHeaders(host=HOST)
    headers["Accept"] = "*/*"
    
    strtoken = requests.get(tokenurl, headers=headers, verify=False).json()["token"]
    url = "https://dms.redbull.tv/v3/linear-borb/%s/playlist.m3u8" % strtoken

    if(url):
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
