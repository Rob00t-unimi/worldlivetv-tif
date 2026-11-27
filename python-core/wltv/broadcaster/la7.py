# -*- coding: utf-8 -*-

from urllib3.exceptions import InsecureRequestWarning
import requests
from lib import scrapers, utils
from lib.broadcaster_result import BroadcasterResult
from time import time

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

HOST = "https://www.la7play.it"
LICENSE_URL = "https://la7.prod.conax.cloud/widevine/license"

PAGES = {
    "La7": "/dirette/la7",
    "La7c": "/dirette/la7-cinema",
}

def _clean(data):
    return data.replace('\\"', '"').replace('\\u0026', '&').replace('\\/', '/')

def play(search):
    res = BroadcasterResult()

    path = PAGES.get(search)
    if not path:
        return res

    headers = utils.getBrowserHeaders(host=HOST)

    data = _clean(requests.get(HOST + path, headers=headers).text)

    url = scrapers.findSingleMatch(data, r'"mainLiveUrl":"([^"]+)"').split("|")[0]
    endpoint = scrapers.findSingleMatch(data, r'"drmTokenEndpoint":"([^"]+)"')
    contentId = scrapers.findSingleMatch(data, r'"drmContentId":"([^"]+)"') or "1"

    if not url or not endpoint:
        return res

    headers["Accept"] = "*/*"

    tokenHeader = headers.copy()
    tokenHeader["dnt"] = "1"
    tokenHeader["te"] = "trailers"

    preAuthToken = requests.get(
        f"{endpoint}?id={contentId}&contentType=LIVE", headers=tokenHeader, verify=False
    ).json()["preAuthToken"]

    licenseHeaders = headers.copy()
    licenseHeaders["content-type"] = "application/octet-stream"
    licenseHeaders["preAuthorization"] = preAuthToken
    licenseHeaders["Origin"] = HOST
    licenseHeaders["Referer"] = HOST + "/"

    licenseConfig = {
        'license_server_url': f'{LICENSE_URL}?d={str(int(time()))}',
        'headers': utils.dict2querystring(licenseHeaders),
        'post_data': 'R{SSM}',
        'response_data': 'R'
    }

    res.Url = url
    res.LicenseKey = '|'.join(licenseConfig.values())
    res.ManifestUpdateParameter = "full"

    return res
