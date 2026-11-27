# -*- coding: utf-8 -*-

import requests, uuid, html, json
from lib import scrapers, config, utils, logger
from .helper import researcher as rs
from lib.broadcaster_result import BroadcasterResult
from time import time

# plugin://plugin.video.wltvhelper/play/generics/search
# plugin://plugin.video.wltvhelper/play/generics/search$chname
# plugin://plugin.video.wltvhelper/play/generics/search$chname$param1

mpd = config.getSetting("mpd")
res = BroadcasterResult()
headers=utils.getBrowserHeaders()


def play(search):
    search = search.lower()
    splitted = search.split('$')
    parameters = []
    
    search = splitted[0]

    parameter1 = ""
    if len(splitted) > 1:
        parameter1 = splitted[1]
        parameters.append(parameter1)
        
    parameter2 = ""
    if len(splitted) > 2:
        parameter2 = splitted[2]
        parameters.append(parameter2)

    options = {
        "goldtv": GetGoldTv,
        "50canale": Get50Canale,
        "noitv": GetNoiTv,
        "teletruria": GetTeletruria,
        "ciaousa": GetCiaoUSA,
        "acisport": GetACI,
        "cilentano": GetCilentano,
        "koper": GetKoper,
        "bandwtv": GetBandw,
        "laq": GetLaqTV,
        "canale88": GetCanale88,
        "canale58": GetCanale58,
        "telenuova": GetTelenuova,
        #"telesardegna": GetTelesardegna,
        "rete8": GetZeroUnoCast,
        "videolina": GetVideoLina,
        "trcmodena": GetTrcModena,
        "rete8sport": GetZeroUnoCast,
        "bike": GetBikeChannel,
        "dacast": GetDacast,
        "tvkappa": GetTvKappa,
        "rtccalabria": GetRTCCalabria,
        "primatvnapoli": GetPrimaTvNapoli,
        "oggisalerno": GetOggiSalerno,
        "cittaceleste": GetCittaCeleste,
        "teleromadue": GetTeleRoma2,
        "telebari": GetTeleBari,
        "sardegnalive": GetSardegnalive,
        "kaloopy": GetKaloopy,
        "7goldemiliaromagna": Get7goldEmiliaRomagna,
        "nolink": GetNoLink,
    }

    if search not in options.keys():
        search = "nolink"

    if len(parameters)>0:
        return options[search](parameters)
    else:
        return options[search]()


def GetNoLink():
    return res

def GetNoLink(params):
    return res


def Get7goldEmiliaRomagna():
    from .helper import webtools
    url = ""

    HOST = "https://www.7goldemiliaromagna.it/diretta-7gold/"
    headers = utils.getBrowserHeaders(host=HOST)

    data = requests.get(HOST, headers=headers).text
    urlInfo = scrapers.findSingleMatch(data, r'<iframe\s+src="([^"]+)"')

    return webtools.GetBroadcasterResult(urlInfo, headers)


def GetVideoLina():
    from .helper import researcher
    url = ""
    HOST = "https://www.videolina.it"
    headers = utils.getBrowserHeaders(host=HOST)
    data = requests.get(f"{HOST}/live", headers=headers).text

    url = researcher.GetLink(data)

    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res


def GetTrcModena():
    from .helper import researcher
    from urllib.parse import urlparse

    url = ""
    HOST = "https://trcmodena.it"
    headers = utils.getBrowserHeaders(host=HOST)
    data = requests.get(f"{HOST}/diretta-streaming", headers=headers).text
    iframeUrl = scrapers.findSingleMatch(data, r'<iframe\b(?=[^>]*\breferrerpolicy="unsafe-url")[^>]*\bsrc="([^"]+)"')

    parsed_url = urlparse(iframeUrl)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    path_parts = parsed_url.path.strip('/').split('/')
    destination_id = path_parts[path_parts.index('destinations') + 1]
    channel_id = path_parts[path_parts.index('channels') + 1]
    
    dataUrl = f'https://api.selftv.video/destinations/{destination_id}/channels/{channel_id}?include=user'
    headers["Referer"] = f"{base_url}/"
    headers["Origin"] = base_url

    data = requests.get(dataUrl, headers=headers).json()
    url = data.get("playback", "").get("hls", "")

    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res


def GetTeletruria():
    from .helper import webtools
    url = ""

    HOST = "https://www.teletruria.it"
    headers = utils.getBrowserHeaders(host=HOST)

    data = requests.get(HOST, headers=headers).text
    urlInfo = scrapers.findSingleMatch(data, r'<iframe\s+src="([^"]+)"')

    return webtools.GetBroadcasterResult(urlInfo, headers)


def GetCiaoUSA():
    url = ""

    HOST = "https://ciaousa.tv"
    APIURL = "https://api.ciaousa.tv/mediaview/api/v1/live/ciao-usa-tv"
    headers = utils.getBrowserHeaders(host=HOST)
    headers["Accept"] = "application/json"
    headers["device_type"] = "web"
    headers["X-REQUEST-TYPE"] = "web"
    headers["X-LANGUAGE-CODE"] = "it"
   
    jsonData = requests.get(APIURL, headers=headers).json()
    
    url = jsonData.get("response", {}).get("hls_url", "")

    if url:
        res.Url = url

    return res


def GetACI():
    url = ""
    HOST = "https://www.acisport.it/aci-sport-tv.asp"
    data = requests.get(HOST, headers=headers).text
    pageUrl = scrapers.findSingleMatch(data, r"iframe\ssrc=\"([^\"]+)")
    data = requests.get(pageUrl, headers=headers).text
    pageUrl = scrapers.findSingleMatch(data, r"\)\.src=\"([^\"]+)")
    dataJson = requests.get(f"{pageUrl}/json", headers=headers).json()
    url = dataJson.get("n3CDNPlaylist", "")

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res


def GetCilentano(params):
    url = ""
    HOST = "https://cilentano.it"

    if not params:
        API = "https://player-backend.restream.io/public/videos/"
        data = requests.get(HOST, headers=headers).text
        token = scrapers.findSingleMatch(data, r'token=([^"]+)')

        jsonData = requests.get(f"{API}{token}", headers=headers).json()
        url = jsonData["videoUrlHls"]

        if mpd:
            url = jsonData["videoUrlDash"]
    else:
        ch = params[0]
        page = f"/cilentano-tv-canale-{ch}/"

        if page:
            data = requests.get(f"{HOST}{page}", headers=headers).text
            pageUrl = scrapers.findSingleMatch(data, r'<iframe.*?litespeed-src="([^"]+)" style')
            data = requests.get(pageUrl, headers=headers).text
            url = scrapers.findSingleMatch(data, r"source\s?src=\"([^\"]+)")
            
        res.UseInputStreamAdaptive = False

    if url:
        res.Url = url

    return res


def GetKoper():
    # Testing after some weeks it did not change
    CLIENT_ID = "82013fb3a531d5414f478747c1aca622"
    API = "https://api.rtvslo.si"

    jsonUrl = f"{API}/ava/getLiveStream/tv.kp1?client_id={CLIENT_ID}"
    jsonData = requests.get(jsonUrl, headers=headers).json()

    urlHost = jsonData.get("response", {}).get("mediaFiles", [])[0].get("streamer", "")
    urlPath = jsonData.get("response", {}).get("mediaFiles", [])[0].get("file", "")

    if urlHost and urlPath:
        res.Url = urlHost + urlPath
        res.UseInputStreamAdaptive = False

    return res


def GetBandw():
    HOST = "https://www.bandw.tv/"
    url = ""

    pageUrl = ""
    data = requests.get(HOST, headers=headers).text
    if data:
        pageUrl = scrapers.findSingleMatch(data, r'<iframe src="([^"]+)"')
    
    if pageUrl:
        data = requests.get(pageUrl, headers=headers).text
        if data:
            url = scrapers.findSingleMatch(data, r"src: '([^']+)'")

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res


def GetLaqTV():
    from . import vimeo

    HOST = "https://www.aqbox.tv/streaming.php"
    data = requests.get(HOST, headers=headers).text
    
    eventId = scrapers.findSingleMatch(data, r'src="[^"]*\/event\/(\d+)')

    # alias = scrapers.findSingleMatch(data, r"mtm_webcam',\s'([^']+)")
    # now = str(int(time()))

    # jsonUrl = f"https://player.ipcamlive.com/player/getcamerastreamstate.php?_={now}&token=&alias={alias}&targetdomain=www.aqbox.tv&getstreaminfo=1"
    # jsonData = requests.get(jsonUrl).json()

    # url0 = jsonData["details"]["address"]
    # url1 = jsonData["details"]["streamid"]
    # url2 = jsonData["streaminfo"]["live"]["levels"][0]["url"]

    # url = f"{url0}streams/{url1}/{url2}".replace("http", "https")

    # if url:
    #     res.Url = url
    #     res.UseInputStreamAdaptive = False

    return vimeo.play(f"l${eventId}")


def GetCanale88():
    url = ""
    REFERER = "https://ott.streann.com"
    HOST = "https://ott 3.streann.com"
    
    source = utils.toBase64("www.nslradiotv.it")
    webPlayerId = "aa85f95b-1551-4851-bc3a-691063421b0b"
    resellerId = "5cb6a1682cdc8fec6b9ae8fd"
    channelId = "5d6001f02cdca9c62bcbf9f6"

    headers = utils.getBrowserHeaders(host=REFERER)

    serverTimeUrl = f"{HOST}/web/services/public/get-server-time"
    serverTime = requests.get(serverTimeUrl, headers=headers).json()["serverTime"]
    serverTime = str(serverTime)

    deviceId = f"{str(uuid.uuid4())}{str(uuid.uuid4())}"
    deviceId = deviceId.replace("-", "")[:50]
    jsonUrl = f"{HOST}/loadbalancer/services/web-players/{webPlayerId}/token/channel/{channelId}/{deviceId}"

    argsData = { "arg1": source, "arg2": utils.toBase64(serverTime) }
    jsonData = requests.post(jsonUrl, headers=headers, data=argsData).json()
    token = jsonData["token"]
    lcltime = int(time() * 1000)

    jsonUrl = f"https://ott3.streann.com/loadbalancer/services/web-players/channels-reseller-secure/{channelId}/{webPlayerId}/{token}/{resellerId}/playlist.m3u8?date={lcltime}&arg1={source}&device-type=web&device-name=web&device-os=web&device-id={deviceId}&doNotUseRedirect=true"
    url = requests.get(jsonUrl, headers=headers).json()["url"]

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res


def GetCanale58():
    from .helper import wimtv
    HOST = "https://www.canale58.com/"
    res =  wimtv.GetWimFromUrl(HOST, 'live')
    res.UseInputStreamAdaptive = True

    return res


def GetOggiSalerno():
    from .helper import wimtv
    HOST = "https://www.tvoggisalerno.it/"

    return wimtv.GetWimFromUrl(HOST, 'live')


def GetTvKappa(params):
    from .helper import wimtv
    HOST = "https://www.tvkappa.it"
    headers = utils.getBrowserHeaders(host=HOST)

    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    ch = params[0] # ch = tvkappa, kairos, keventi

    postData = {
        "version": "225-325", 
        "__ca":"33",
        "f": "getPage",
        "page": f"popup/{ch}.xml",
        "lang": "it"
    }

    data = requests.post(f"{HOST}/manager/includer.php", headers=headers, data=postData).text

    return wimtv.GetWimFromData(data, 'cast')


def GetKaloopy():
    HOST = "https://www.distro.tv"
    streamPage = "https://tv.jsrdn.com/tv_v5/show.php?name=kaloopy"
    headers = utils.getBrowserHeaders(host=HOST)
    jsonData = requests.get(streamPage, headers=headers).json()
    key = jsonData.get("topics", {}).get("shows", [])[0]
    url = jsonData.get("shows", {}).get(str(key), {}).get("seasons", [])[0].get("episodes", [])[0].get("content", {}).get("url", "")
    
    if url:
        res.Url = url
        res.StreamHeaders = headers

    return res


def GetRTCCalabria():
    from .helper import researcher
    HOST = "https://www.mediastreaming.it/c3/player.htm"
    headers = utils.getBrowserHeaders(host=HOST)
    data = requests.get(HOST, headers=headers).text
    #url = scrapers.findSingleMatch(data, r'"source":\s?"([^"]+)')
    url = researcher.GetLink(data)
    
    if url:
        res.Url = url

    return res


def GetPrimaTvNapoli():
    HOST = "https://www.primatvnapoli.com/"
    headers = utils.getBrowserHeaders(host=HOST)
    data = requests.get(HOST, headers=headers).text
    jsonData = scrapers.findSingleMatch(data, r'<div[^>]*class="[^"]*player[^"]*"[^>]*>\s*<div[^>]*data-item="([^"]*)"[^>]*>')
    jsonData = html.unescape(jsonData)
    
    url = ""
    try:
        jsonData = json.loads(jsonData)
        sources = jsonData.get('sources', [])

        for source in sources:
            if 'mpegurl' in source.get('type', ''):
                url = source.get('src', '')
                break 
    except :
        pass

    if url:
        res.Url = url

    return res


def Get50Canale():
    from .helper import restream
    HOST = "https://50canale.tv/"
    headers = utils.getBrowserHeaders(host=HOST)
    dash = False
    data = requests.get(HOST, headers=headers).text
    token = scrapers.findSingleMatch(data, r'<iframe[^>]*src="[^"]*\?token=([^"&]+)')
    return restream.GetUrl(token, dash)


def GetNoiTv():
    from .helper import restream
    HOST = "https://noitv.it/"
    headers = utils.getBrowserHeaders(host=HOST)
    dash = False
    data = requests.get(f"{HOST}live", headers=headers).text
    token = scrapers.findSingleMatch(data, r'<iframe[^>]*src="[^"]*\?token=([^"&]+)')
    return restream.GetUrl(token, dash)


def GetTelenuova():
    from .helper import wimtv
    HOST = "https://telenuova.tv/"

    data = requests.get(HOST, headers=headers).text
    pageUrl = scrapers.findSingleMatch(data, r'<a\s+href="([^"]+)"[^>]*>\s*DIRETTA TV\s*</a>')
    data = None
    chId = utils.getGuid(pageUrl)

    return wimtv.GetWimUrlByChId(chId)


def GetZeroUnoCast(params):
    url = ""
    ch = params[0]
    pageUrl = f"https://zerounocaststreaming.it:2020/VideoPlayer/{ch}"
    data = requests.get(pageUrl, headers=headers).text
    url = rs.GetLink(data)

    if url:
        res.Url = url

    return res


def GetTeleBari():
    url = ""
    pageUrl = "https://www.telebari.it/player_html5/clap.html"
    data = requests.get(pageUrl, headers=headers).text
    url = rs.GetLink(data)

    if url:
        res.Url = url

    return res
    

def GetTeleRoma2():
    url = ""
    pageUrl = "https://www.teleromadue.it/"
    data = requests.get(pageUrl, headers=headers).text
    url = rs.GetLink(data)

    if url:
        res.Url = url

    return res


def GetCittaCeleste():
    url = ""
    HOST = "https://cittaceleste.tv"

    data = requests.get(HOST, headers=headers).text
    data = ''.join(data.splitlines())

    pageUrl = scrapers.findSingleMatch(data, r'location\.href=\'([^\']*)\';[^>]*>[\s\S]*?Live Streaming')
    pageUrl = f"{HOST}{pageUrl}"
    data = requests.get(pageUrl, headers=headers).text
    url = rs.GetLink(data)
    url = url.replace('\n', '')
    
    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res

def GetSardegnalive():
    from .helper import livepush

    pageUrl = "https://www.sardegnalive.net/webtv"
    data = requests.get(pageUrl, headers=headers).text
    
    videoId = scrapers.findSingleMatch(data, r'<iframe[^>]*?livepush[^>]*?/([^/"]+)"')

    return livepush.GetLivepush(videoId)


def GetBikeChannel():
    url = ""
    HOST = f"https://bikechannel.it"
    headers = utils.getBrowserHeaders(host=HOST)

    data = requests.get(f"{HOST}/live-tv.html", headers=headers).text
    url = scrapers.findSingleMatch(data, r'<source\s+type="application/x-mpegURL"\s+src="([^"]+)"')
    
    if url:
        res.Url = url
        res.StreamHeaders = headers
        res.UseInputStreamAdaptive = False

    return res
    
   
def GetDacast(param):
    from .helper import dacast
    return dacast.GetDacastUrl(param)


def GetGoldTv(params):
    url = ""
    HOST = "https://www.goldtv.it"
    par = params[0]
    page = "gold-tv-italia"

    if   par == "ita":
        page = "gold-tv-italia"
    elif par == "sat":
        page = "gold-tivu-sat"
    elif par == "lcn":
        page = "gold-tv-lcn-11"
    
    headers = utils.getBrowserHeaders(host=HOST)
    data = requests.get(f"{HOST}/canali/{page}", headers=headers).text
    url = rs.GetLink(data)

    if url:
        res.Url = url
        res.UseInputStreamAdaptive = False

    return res
