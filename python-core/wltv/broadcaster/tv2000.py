# -*- coding: utf-8 -*-

import requests
from lib import scrapers, xmltodict, logger
from lib.broadcaster_result import BroadcasterResult


# HOST = "https://diretta.tv2000.it/"
# DRM_API_URL = "api/drm/status"
# LIVE_CHANNEL_URL = "?channel=tv2000_live"
M3U8_XML_URL = "https://data.meride.tv/proxy/bulkproxynew/embedproxy_bulk.php/{}/play2000/desktop/preroll-play2000/f4m/default/aHR0cHM6Ly93d3cucGxheTIwMDAuaXQvKg=="
                                     


def play(search):
    res = BroadcasterResult()

    url = ""
    idChannel = "4Y3ZMmvcvo"
    # var2Find = ""
    # widevineLicenseUrl = "https://widevine-dash.ezdrm.com/proxy?pX=A90BE1"

    # isDrmJson = requests.get(f"{HOST}{DRM_API_URL}").json()
    # isDrm = isDrmJson["active"] == "true"
    # strXml = ""

    # data = requests.get("{}{}".format(HOST, LIVE_CHANNEL_URL)).text

    # if isDrm:
    #     var2Find = "playreadyEmbedID"
    #     res.UseInputStreamAdaptive = True
    # else:
    #     var2Find = "nonRestrictedEmbedID"
    #     res.UseInputStreamAdaptive = False

    # idChannel = scrapers.findSingleMatch(data, r'var\s{}\s=\s"(.*?)"'.format(var2Find))

    strXml = requests.get(M3U8_XML_URL.format(idChannel)).text
    xml = xmltodict.parse(strXml)
    url = xml["embed"]["video"]["default"]

    if url:
        res.Url = url

    return res
