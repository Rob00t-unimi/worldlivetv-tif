# -*- coding: utf-8 -*-

from urllib3.exceptions import InsecureRequestWarning

import xbmcgui, uuid, requests, json
from collections import namedtuple
from urllib.parse import urlencode, unquote, quote
from lib import xmltodict, config, utils, scrapers, logger, const, wltvcache
from lib.broadcaster_result import BroadcasterResult

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
cacheKey = "MediaserAppInfo"

AppInfo = namedtuple("AppInfo", ["appName", "appVersion", "build", "version", "ssoKey", "sid", "token"])
APIKEY = "3_l-A-KKZVONJdGd272x41mezO6AUV4mUoxOdZCMfccvEXAJa6COVXyT_tUdQI03dh"
WIDEVINE_ACCOUNT = 2702976343

HOST = "https://mediasetinfinity.mediaset.it"
LOGIN_URL = "https://login.mediaset.it"
API_HOST = "https://api-ott-prod-fe.mediaset.net"

regex_appname = r'"app-name" content="([^"]+)'
regex_appversion = r'"app-version" content="([^"]+)'
regex_build = r'"number":\s*([0-9]+)'
regex_version = r'"version":\s*"([^"]+)"'
regex_ssoKey = r'"ssoKey":\s*"([^"]+)"'

clientId = str(uuid.uuid1())

#LOGIN_ANONIMOUS_API_URL  = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/anonymous/login/v2.0"
#ACCEDO_URL = "https://api.one.accedo.tv/session?appKey=6023de431de1c4001877be3b&uuid={uuid}&gid=default"

#ALLSTATION_URL = "https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations-v2?sort=shortTitle|asc&form=cjson&httpError=true"
ALLSTATION_URL = "https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations-v2?sort=shortTitle|asc&fields=guid,callSign,title,tuningInstruction&form=cjson&httpError=true"
LICENSE_URL = "https://widevine.entitlement.theplatform.eu/wv/web/ModularDrm/getRawWidevineLicense?releasePid={pid}&account=http://access.auth.theplatform.com/data/Account/{wvaccount}&schema=1.0&token={token}"

#STREAM_URL  = "https://api-ott-prod-fe.mediaset.net/PROD/play/playback/check/v2.0?sid={sid}"
ALL_JSON = "https://static3.mediasetplay.mediaset.it/apigw/nownext/nownext.json"

streamDataResponse = {"dash":{"url":"","pid":"","isWidevine":False },"mpeg":{"url":"","pid":"","isWidevine":False }}

headers = utils.getBrowserHeaders(host=HOST)


def play(search):
    res = BroadcasterResult()
    appInfo = getAppInfo()

    url = ""
    pid = ""
    callSign = getCallSign(search)
    
    streamDataRes = getWebBrowserStreamData(appInfo, callSign)

    forceMpd = False
    url = streamDataRes["mpeg"]["url"]

    if not url: 
        forceMpd = True
        url = streamDataRes["dash"]["url"]
        widevine = streamDataRes["dash"]["isWidevine"]
        pid = streamDataRes["dash"]["pid"]

    if "theplatform" in url:
        url = requests.get(url, headers=headers).url

    if url:
        licenseHeaders = headers.copy()

        if forceMpd:
            res.ManifestUpdateParameter = "full"
            licenseHeaders["Accept"] = "*/*"
            licenseHeaders["Content-Type"] = "application/octet-stream"

            licenseConfig = { 
                'license_server_url': LICENSE_URL.format(pid=pid, wvaccount=WIDEVINE_ACCOUNT, token=appInfo.token),
                'headers': utils.dict2querystring(licenseHeaders),
                'post_data': 'R{SSM}',
                'response_data': 'R'
            }

            if widevine and pid:
                res.LicenseKey = '|'.join(licenseConfig.values())
        else:
            res.UseInputStreamAdaptive = False

        res.UserAgent = True
        res.Url = url
    else:
        logger.error("No url found for: ", search)
    
    return res

def getAppInfo():
    _appInfo = None
    strAppInfo = wltvcache.get_or_set_string(cacheKey)

    if strAppInfo:
        _dict = json.loads(strAppInfo)
        _appInfo = AppInfo(**_dict)

    if _appInfo and utils.isJwtExpired(_appInfo.token):
        strAppInfo = None

    if not strAppInfo:
        username = config.getSetting("MediasetUsername")
        password = config.getSetting("MediasetPassword")

        # if username and password:
        #     _appInfo = loginresult(username, password)
        # else:
        #     _appInfo = loginresultAnonymous()
        _appInfo = loginresultAnonymous()

        strAppInfo = json.dumps(_appInfo._asdict())
        wltvcache.get_or_set_string(cacheKey, strAppInfo, 24*60)
        
    if not _appInfo:
        _dict = json.loads(strAppInfo)
        _appInfo = AppInfo(**_dict) 

    return _appInfo

def loginresultAnonymous():
    session, appInfo = initSessionAndGetAppInfo()

    appName = appInfo.appName
    appVersion = appInfo.appVersion
    build = appInfo.build
    version = appInfo.version
    ssoKey = appInfo.ssoKey

    url = f"{API_HOST}/PROD/play/idm/anonymous/login/v2.0"

    session.headers.update({"Content-Type": "application/json"})
    jsonData = {"appName":appName, "client_id":clientId}
    data = session.post(url, json=jsonData).json()

    sid = data["response"]["sid"]
    beToken = data["response"]["beToken"]

    appInfo=appInfo._replace(sid = sid)
    appInfo=appInfo._replace(token = beToken)
    
    return appInfo

def loginresult(username, password):
    session, appInfo = initSessionAndGetAppInfo()

    appName = appInfo.appName
    appVersion = appInfo.appVersion
    build = appInfo.build
    version = appInfo.version
    ssoKey = appInfo.ssoKey

    session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
    encodedPageURL = quote(f"{HOST}", safe='')
    formData = f"loginID={username}&password={password}&sessionExpiration=31536000&targetEnv=jssdk&include=profile%2Cdata%2Cemails%2Csubscriptions%2Cpreferences%2Cid_token%2Cdata.fastLoginPIN%2Cdata.civico%2C&includeUserInfo=true&loginMode=standard&lang=it&riskContext=%7B%22b0%22%3A4805%2C%22b1%22%3A%5B21%2C14%2C41%2C7%5D%2C%22b2%22%3A4%2C%22b3%22%3A%5B%5D%2C%22b4%22%3A2%2C%22b5%22%3A1%2C%22b6%22%3A%22{const.USER_AGENT}%22%2C%22b7%22%3A%5B%7B%22name%22%3A%22PDF%20Viewer%22%2C%22filename%22%3A%22internal-pdf-viewer%22%2C%22length%22%3A2%7D%2C%7B%22name%22%3A%22Chrome%20PDF%20Viewer%22%2C%22filename%22%3A%22internal-pdf-viewer%22%2C%22length%22%3A2%7D%2C%7B%22name%22%3A%22Chromium%20PDF%20Viewer%22%2C%22filename%22%3A%22internal-pdf-viewer%22%2C%22length%22%3A2%7D%2C%7B%22name%22%3A%22Microsoft%20Edge%20PDF%20Viewer%22%2C%22filename%22%3A%22internal-pdf-viewer%22%2C%22length%22%3A2%7D%2C%7B%22name%22%3A%22WebKit%20built-in%20PDF%22%2C%22filename%22%3A%22internal-pdf-viewer%22%2C%22length%22%3A2%7D%5D%2C%22b8%22%3A%2219%3A06%3A05%22%2C%22b9%22%3A-60%2C%22b10%22%3A%7B%22state%22%3A%22prompt%22%7D%2C%22b11%22%3Afalse%2C%22b12%22%3A%7B%22charging%22%3Atrue%2C%22chargingTime%22%3A0%2C%22dischargingTime%22%3Anull%2C%22level%22%3A1%7D%2C%22b13%22%3A%5Bnull%2C%222560%7C1440%7C24%22%2Cfalse%2Ctrue%5D%7D&APIKey={APIKEY}&cid=mediaset-web-%20Default&source=showScreenSet&sdk=js_latest&authMode=cookie&pageURL={encodedPageURL}&sdkBuild={build}&format=json"
    data = session.post(f"{LOGIN_URL}/accounts.login", data=formData).json()

    del data["preferences"]
    del data["profile"]
    del data["subscriptions"]
    del data["userInfo"]
    id_token = data["id_token"]

    url = f"{API_HOST}/PROD/play/idm/account/login/v2.0"
    
    session.headers.update({"Accept": "application/json, text/plain, */*"})
    session.headers.update({"Content-Type": "application/json;charset=UTF-8"})
    jsonData = {"appName":appName, "client_id":clientId, "include":"personas,adminBeToken", "gt":id_token}
    data = session.post(url, json=jsonData).json()
    
    sid = data["response"]["sid"]
    caToken = data["response"]["caToken"]
    personasId =  data["response"]["account"]["personas"][0]["id"]
    
    url = f"{API_HOST}/PROD/play/idm/persona/login/v2.0?sid={sid}"
    
    jsonData = { "id": personasId, "caToken": caToken }
    data = session.post(url, json=jsonData).json()
    beToken = data["response"]["beToken"]

    appInfo=appInfo._replace(sid = sid)
    appInfo=appInfo._replace(token = beToken)

    return appInfo
    
def initSessionAndGetAppInfo():
    session = getSession()

    data = session.get(HOST).text

    appName = scrapers.findSingleMatch(data, regex_appname)
    appVersion = scrapers.findSingleMatch(data, regex_appversion)

    url = f"https://cdns.gigya.com/JS/gigya.js?&lang=it-it&apiKey={APIKEY}&enableSSOToken=false"
    data = session.get(url).text
    build = scrapers.findSingleMatch(data, regex_build)
    version = scrapers.findSingleMatch(data, regex_version)

    url = f"{LOGIN_URL}/gs/webSdk/Api.aspx?apiKey={APIKEY}&version=latest&build=16798&serviceName=apiService"
    data = session.get(url).text
    ssoKey = scrapers.findSingleMatch(data, regex_ssoKey)

    encodedPageURL = quote(f"{HOST}", safe='')
    url = f"{LOGIN_URL}/accounts.webSdkBootstrap?apiKey={APIKEY}&pageURL={encodedPageURL}&sdk=js_latest&sdkBuild={build}&format=json"
    
    session.get(url)
    _appInfo = AppInfo(appName, appVersion, build, version, ssoKey, '', '')

    return session, _appInfo 

def getCallSign(search):
    callSign = ""

    if search.startswith("$"): 
        callSign = search[1:]
    else:
        items = requests.get(ALLSTATION_URL, headers=headers).json()["entries"]
        for item in items:
            if search.startswith("$"):
                _search = "$" + item["callSign"]
            else:
                _search = item["title"]

            if item.get("tuningInstruction", "") and _search == search:
                callSign = item["callSign"]
                break

        items = None

    return callSign

def getSession():
    session = requests.Session()
    session.headers.update(headers)
    return session

def getWebBrowserStreamData(appInfo, callSign):
    _headers = headers.copy()
    _headers["Authorization"] = f"Bearer {appInfo.token}"
    _headers["Accept"] = "application/json, text/plain, */*"
    _headers["Content-Type"] = "application/json"
    session = getSession()
    session.headers.update(_headers)

    jsonStreamRequestData = {
        "channelCode": callSign,
        "streamType": "LIVE",
        "delivery": "Streaming",
        "createDevice": "true",
        "overrideAppName": appInfo.appName
    }
    
    url = f"{API_HOST}/PROD/play/playback/check/v2.0?sid={appInfo.sid}"
    #jsonStream = session.post(STREAM_URL.format(sid=sid), json=jsonStreamRequestData).json()
    jsonStream = session.post(url, json=jsonStreamRequestData).json()
    #logger.debug("jsonStream:", jsonStream)

    parameters = jsonStream["response"]["mediaSelector"]
    parameters["auth"] = appInfo.token
    
    streamUrl = parameters.pop("url")
    streamUrl  = f"{streamUrl}?{unquote(urlencode(parameters))}"
    
    _headers["Authorization"] = ''
    _headers["Content-Type"] = ''
    session.headers.update(_headers)
    smilXml = session.get(streamUrl).content.decode()

    #logger.debug("smil:", smilXml)
    xml = xmltodict.parse(smilXml)
    ref = xml["smil"]["body"]["seq"]["switch"]["ref"]
    par = ref["param"]
    url = ref["@src"] 
    
    isEncrypted = False if not "@security" in ref else ref["@security"] == "commonEncryption"
    pid = scrapers.findSingleMatch(par["@value"], r"\|pid=([^|]+)")

    isDash = ".mpd" in url
    
    k = "dash" if isDash else "mpeg"
    streamDataResponse[k]["isWidevine"] = isEncrypted
    streamDataResponse[k]["pid"] = pid
    streamDataResponse[k]["url"] = url
    
    return streamDataResponse


def getManualStreamData(session, headers, search):
    global token, streamDataResponse

    items = session.get(ALLSTATION_URL, headers=headers).json()["entries"]

    streamDataResponse = {"dash":{"url":"","pid":"","isWidevine":False },"mpeg":{"url":"","pid":"","isWidevine":False }}
    
    # search
    for item in items:
        title = item["title"]
        if search.startswith("$"):
            _search = "$" + item["callSign"]
        else:
            _search = item["title"]

        tu = item.get("tuningInstruction")
        if tu and _search == search:

            for key in tu.get("urn:theplatform:tv:location:any"):
                isDash = False
                isMpeg = False

                strmFormat = "dash+xml"
                if key["format"] == "application/{}".format(strmFormat):
                    isDash = True
                else:
                    strmFormat = "x-mpegURL"
                    if key["format"] == "application/{}".format(strmFormat):
                        isMpeg = True

                if isDash or isMpeg:
                    try:
                        if "geoIT" in key["assetTypes"]: # or "geoNo" in key["assetTypes"] or "geoNoLim" in key["assetTypes"]:
                            k = "dash" if isDash else "mpeg"
                            if not streamDataResponse[k]["url"]:
                                streamDataResponse[k]["isWidevine"] = "widevine" in key["assetTypes"]
                                streamDataResponse[k]["pid"] = key["releasePids"][0]
                                streamDataResponse[k]["url"] = key["publicUrls"][0]
                    except:
                        logger.error(f"No PublicUrls for '{title}' with format {strmFormat}")

                if streamDataResponse["dash"]["url"] and streamDataResponse["mpeg"]["url"]:
                    break

    items = item = key = None
    
    return streamDataResponse
