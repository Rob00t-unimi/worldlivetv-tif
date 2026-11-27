# -*- coding: utf-8 -*-
import requests

from lib import utils, scrapers, logger
from lib.broadcaster_result import BroadcasterResult

fileName = "ListSamsungTv.bin"
StreamBaseUrl = "https://jmp2.uk/"

def play(search):
    res = BroadcasterResult()

    user_agent_default = "HbbTV/1.2.1 (+DRM;Samsung;SmartTV2016;T-JZMDEUC-1243.2;;) WebKit"
    slug_default = "stvp-{id}"
    channel_info = {}

    headers = utils.getBrowserHeaders()
    jsonData = utils.GetJsonList(fileName, False)

    if jsonData:
        slug = jsonData.get("slug", "")
        user_agent = jsonData["headers"].get("user-agent", "")
        channel_info = jsonData["regions"]["it"]["channels"].get(search, {})

    user_agent = user_agent or user_agent_default

    if user_agent:
        headers["User-Agent"] = user_agent

    if channel_info:
        licenseKey = channel_info.get("headers", {}).get("Authorization", "")
        licenseUrl = channel_info.get("license_url", "")
        licenseConfig = { 
            'license_server_url': licenseUrl,
            'headers': utils.dict2querystring(headers),
            'post_data': 'R{SSM}',
            'response_data': 'R'
        }
        res.LicenseKey = '|'.join(licenseConfig.values())

        #res.StreamHeaders = headers
        #res.LicenseKey = f"{licenseUrl}|{licenseKey}|R{{SSM}}|"
        #res.LicenseKey = licenseUrl

    slug = slug or slug_default
    url = f"{StreamBaseUrl}{slug}".format(id=search)

    res.Url = url
    res.Headers = headers
    res.UseInputStreamAdaptive = True

    return res
