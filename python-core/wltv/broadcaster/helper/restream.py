# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult


def GetUrl(token, getDash):
    res = BroadcasterResult()
    url = ""

    HOST = "https://player-backend.restream.io"
    channelInfo = f"{HOST}/public/status-connection-data/{token}"

    headers = utils.getBrowserHeaders()

    # eventId = ""
    # data = requests.get(channelInfo, headers=headers).json()
    # for event in data["eventsInProgress"]:
    #     if "Restream" in event["title"]:
    #         eventId = event["id"]

    #streamInfo = f"{HOST}/public/videos/{token}?event-id={eventId}"
    streamInfo = f"{HOST}/public/videos/{token}?instant=true"
    data = requests.get(streamInfo, headers=headers).json()

    if getDash:
        url = data["videoUrlDash"]
    else:
        url = data["videoUrlHls"]

    if url:
        res.Url = url
        #res.UseInputStreamAdaptive = True
        res.StreamHeaders = headers

    return res