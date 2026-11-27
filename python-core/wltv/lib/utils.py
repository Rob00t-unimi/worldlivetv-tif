import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon
import sys
import json
import base64
import zlib
import requests
import time
import datetime
import hashlib
import urllib
import uuid
import importlib
import socket
import time

from xbmcvfs import translatePath
from urllib import request
from urllib.parse import urlencode
from typing import List
from lib import config, logger, scrapers, install, const
from lib.customlist import CustomList, ListType
from lib.m3u.m3ulist import M3UList
from lib.m3u.m3uitem import M3UItem
from lib.playablemediaitem import PlayableMediaItem
from lib.timeoutpath import TimeoutPath

ADDON_NAME = "World Live TV"

HOST = "https://www.worldtvlive.eu"
HOST_TVCH = "https://tvchannels.worldtvlive.eu"

API_DOMAIN = f"{HOST_TVCH}/tv"
FILE_REPO_URL = f"{HOST}/world/files"
ADDON_REPO_HOTFIX = "https://worldlivetv.github.io/repo/plugin.video.wltvhelper.hotfix"
EPG_URL = "http://epg-guide.com/wltv.xz"
EPG_FILE_NAME = "wltv.xz"
VIDEO_NOT_FOUND = "https://worldlivetv.github.io/not_found.mp4"
LAST_CHK_INF = "lastcheck.inf"
SETTINGS_FILE = "settings.xml"
HOTFIX_FILE = "hotfix.zip"
HOTFIX_FILE_INFO = "hotfix.json"

EMR_LIST_FILE = "emr.bin"
TEMP_LISTFILE_NAME = "~temp.bin"

EMPTY_FILE = "empty.bin"
EMPTY_EPG_FILE_NAME = "empty.gz"

TEMP_FULL_USERLISTFILE_NAME = "~tempFullUser.bin"
TEMP_USERLISTFILE_NAME = "~tempUser.bin"

DEFAULT_DATE = 20210101
UNSUPPORTED_KODI_VERSION = 19

PARAM_LIST_NAME = "personal_list_v1"
PARAM_USER_LIST_NAME = "user_list_v1"
EXPIRING_LOCAL_FILES_DAYS = config.getSetting("localFileExpiringDays")
TAG_ADDON_KODILIST = "kodi"

BETA_TOKEN = "566796c646c627f677"


def MessageBox(msg: str):
    if isinstance(msg, int):
        msg = config.getString(msg)
    xbmcgui.Dialog().ok(ADDON_NAME, msg)

def MessageBoxQuestion(msg: str):
    if isinstance(msg, int):
        msg = config.getString(msg)
    return xbmcgui.Dialog().yesno(ADDON_NAME, msg)

def MessageNotification(msg: str, seconds: int = 0):
    if isinstance(msg, int):
        msg = config.getString(msg)
    xbmcgui.Dialog().notification(ADDON_NAME, message = msg, time = seconds * 1000)

def MessageBoxInput(msg: str, inputStr: str = ""):
    if isinstance(msg, int):
        msg = config.getString(msg)
        if not msg: msg = ADDON_NAME
    return xbmcgui.Dialog().input(msg, inputStr, type = xbmcgui.INPUT_ALPHANUM)


def getBrowserHeaders(includeInsecureRequests = False, host = "") -> dict:
    headers = {
        "User-Agent": const.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6"
        #"Accept-Encoding": "gzip, deflate, br, zstd ", # <== needs to decompress response (to test)
    }

    if host != "":
        headers["Origin"] = host
        headers["Referer"] = f"{host}/"

    if includeInsecureRequests:
        headers["Upgrade-Insecure-Requests"] = "1"

    return headers


def updateHeaders(headers, newHeaders):
    newDict = dict(urllib.parse.parse_qsl(headers))
    newDict.update(newHeaders)
    return urlencode(newDict)


def dict2querystring(d):
    _pairs = [f"{k}={v}" for k, v in d.items()]
    qs = "&".join(_pairs)
    return qs


def apiRequester(par=""):
    return requests.get(API_DOMAIN + par, timeout=5).json()


def getScriptFileName(fileName):
    return os.path.splitext(os.path.basename(fileName))[0]


def checkServerOnLine():
    res = False
    isOnLine = False

    if config.getSetting("emulateServerOffLine") and config.isBeta() == True:
        logger.info("Emulation Server off-line is set to True")
        return res

    try:
        isOnLine = requests.get(HOST_TVCH + "/online", timeout=5).status_code
        res = isOnLine == 204
    except Exception as ex:
        logger.error(ex)
        pass

    if not res:
        logger.info(f"Server off-line or server error - status code: {isOnLine}")

    return res


def isOnline(test_url="https://www.google.com", timeout=2):
    try:
        response = requests.get(test_url, timeout=timeout)
        return response.status_code == 200
    except Exception as ex:
        return False


def maskIp(ip_address, mask_octets_number=2):
    """
    Masks the specified number of octets in an IP address with '***'.

    :param ip_address: The IP address as a string (e.g., '192.168.1.123')
    :param mask_octets_number: The number of octets to mask (default is 2)
    :return: The masked IP address (e.g., '192.168.***.***')
    """
    try:
        # Split the IP address into octets
        octets = ip_address.split(".")

        oLen = len(octets)
        # Ensure it's a valid IPv4 address with 4 octets
        if oLen != 4:
            raise ValueError("Invalid IP address format")

        # Mask the specified number of octets
        for i in range(oLen - mask_octets_number, oLen):
            octets[i] = "***"

        # Join the octets back together
        return ".".join(octets)
    except Exception as e:
        # Handle invalid IP addresses
        return f"Error: {str(e)}"


def getIp():
    res = requests.get('https://api.ipify.org?format=json')
    res.raise_for_status()
    ip = res.json()['ip']

    return ip


def getIpInfo():
    ip = getIp()

    res = requests.get(f'https://ipinfo.io/{ip}/json')
    res.raise_for_status()
    nfo = res.json()

    return nfo


def isItaly():
    rc = False
    try:
        geoInfo = getIpInfo()
        ip = geoInfo.get('ip')
        country = geoInfo.get('country')

        rc = country == 'IT'
        if rc:
            ip = maskIp(ip)
            logger.info(f"Italy IP detected, IP: {ip}")
        else:
            logger.info(f"Not Italy IP detected, IP: {ip}, Country: {country}, City: {geoInfo.get('city')}")
    except Exception as e:
        logger.error(f"Error during isItaly info request: {e}")

    return rc

def getTimestamp(inMs = True):
    from datetime import datetime
    now = datetime.utcnow()

    _timestamp = now.timestamp()
    if inMs:
        return int(_timestamp * 1000)

    return int(_timestamp)

def isGzFile(filepath):
    with open(filepath, 'rb') as tmpFile:
        return tmpFile.read(2) == b'\x1f\x8b'


def isXzFile(filepath):
    with open(filepath, 'rb') as tmpFile:
        return tmpFile.read(5) == b'\xfd\x37\x7a\x58\x5a'


def decompressGZFile(infile: str, tofile: str):
    import gzip
    with open(infile, 'rb') as inf:
        _str = gzip.decompress(inf.read()).decode('utf-8')

    with open(tofile, 'w', encoding='utf8') as tof:
        tof.write(_str)

def GetJsonList(fileName, sendNotification = True):
    jsonData = None

    try:
        jsonData = getContentResource(fileName)
        jsonData = json.loads(jsonData)
    except Exception as e:
        jsonData = None
        logger.error("GetJsonList error:", e)

    if not jsonData and sendNotification:
        MessageNotification(config.getString(30148))

    return jsonData

def readFile(fullFileName):
    file = xbmcvfs.File(fullFileName)
    fileContent = file.read()
    file.close()

    return fileContent


def readFileAllRows(fullFileName):
    l = list()
    with open(fullFileName, 'r') as f:
        l = f.readlines()
        f.close()

    return l


def writeFile(filePath, input):
    file = xbmcvfs.File(filePath, "wb")  # Use "wb" mode for writing binary files
    if isinstance(input, bytes):
        file.write(input)  # Write binary data directly
    else:
        file.write(input.encode('utf-8'))  # Encode strings to binary before writing
    file.close()


def getOrUpdateEpg():
    epgPath, isBanned, needsEpgUpdate = getOrUpdateEpgResult()
    return epgPath


def getOrUpdateEpgResult():
    epgPath = getPersonalSubPathFile("", EPG_FILE_NAME)
    isBanned = False
    needsEpgUpdate = False

    if not checkFileExists(epgPath) or not isXzFile(epgPath) or localFileNeedsUpdate(epgPath, 1):
        isBanned = checkIsBanned(epgPath)
        if not isBanned:
            headers = getBrowserHeaders()
            headers["User-Agent"] = f"WLTV {const.USER_AGENT}"
            content, resStatus = downloadFile(EPG_URL, epgPath, headers=headers)
            if resStatus == 429:
                isBanned = True
                logger.error(f"Error downloading EPG file => status: {resStatus}")
            needsEpgUpdate = resStatus == 200
        
        if isBanned:
            logger.error(f"Error downloading EPG file => isBanned")

    return epgPath, isBanned, needsEpgUpdate


def checkIsBanned(epgPath):
    res = False
    if checkFileExists(epgPath) and not isXzFile(epgPath):
        fileExpiredDate = datetime.datetime.fromtimestamp(os.path.getmtime(epgPath)) + datetime.timedelta(hours=1)
        dtExpFile = int(fileExpiredDate.strftime("%Y%m%d%H%M"))
        dtNow = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
        res = dtNow < dtExpFile

    return res


def getOrUpdateEmergencyList():
    emr = getPersonalSubPathFile("", EMR_LIST_FILE)

    if localFileNeedsUpdate(emr, 5):
        readLocalOrDownload(FILE_REPO_URL, "", EMR_LIST_FILE, False)

    return emr


def downloadFile(url, filePath, returnContent=False, headers: dict=None, timeout=None):
    """
    Downloads a file from a given URL. Optionally returns the file content if returnContent is True.
    Handles status code 429 (Too Many Requests) and other potential errors gracefully.
    """
    fileContent = ""
    status = 0

    try:
        req = requests.get(url, allow_redirects=True, headers=headers, timeout=timeout)
        status = req.status_code
        if status == 429:  # Too Many Requests
            logger.error(f"Request '{url}' blocked due to rate limiting (HTTP 429). Please try again later.")
            #return None  # Optionally, return an empty content or an error indicator
        elif status != 200:  # Other non-success statuses
            logger.error(f"Failed to download file. HTTP status code: {status}")
            #return None
        else:
            # If the request is successful (status code 200), proceed
            fileContent = req.content
    except Exception as ex:
        logger.error(f"An error occurred while downloading from url '{url}': {ex}")

    if filePath:
        writeFile(filePath, fileContent)

    if returnContent:
        return fileContent, status

    return '', status


def downloadFtpFile(url, ftp_user, ftp_password, filePath, returnContent=False, headers: dict = None, timeout = None):  # duplice funzione, returnContent ritorna anche il contenuto
    import io
    from ftplib import FTP

    fileContent = ""
    try:
        parsed_url = urllib.parse.urlparse(url)
        ftp = FTP(parsed_url.hostname, timeout = 10)

        if not ftp_user:
            ftp_user = parsed_url.username or "anonymous"  # Default "anonymous" if not specified
            ftp_password = parsed_url.password or ""

        ftp.login(ftp_user, ftp_password)

        ftp.cwd(os.path.dirname(parsed_url.path))
        with io.BytesIO() as buffer:
            ftp.retrbinary(f'RETR {os.path.basename(parsed_url.path)}', buffer.write)
            buffer.seek(0)
            fileContent = buffer.read()  # Read the content as bytes

        ftp.quit()
    except :
        pass

    if filePath:
        writeFile(filePath, fileContent)
    if returnContent:
        return fileContent


def extract(zipFilePath, destination):  # alternative to xbmc.executebuiltin(Extract
    import zipfile  # non serve altrove

    with zipfile.ZipFile(zipFilePath, "r") as zip:
        zip.extractall(destination)


def getPersonalPathFile(filename):
    filePath = os.path.join(config.ADDON_USER_PATH, filename)

    return translatePath(filePath)


def getPersonalSubPathFile(subDir, filename):
    filePath = os.path.join(config.ADDON_USER_PATH, subDir, filename)

    return translatePath(filePath)


def createSubDir(subDir):
    if subDir:
        path = translatePath(os.path.join(config.ADDON_USER_PATH, subDir))
        if not os.path.isdir(path):
            os.mkdir(path)


def getFiles(dir: str = config.ADDON_USER_PATH, searchPattern: str = "*") -> list():
    import glob

    files = list()
    dirPath = translatePath(dir)
    patterns = searchPattern.split(",")

    for ext in patterns : files.extend(glob.glob(dirPath + ext))

    return list(set(files))


def readLocalOrDownload(repoUrl, subDir, fileName, sameRemoteSub = False, checkServerFileTimeStamp = True, onceaday = True):
    fileContent = ""
    createSubDir(subDir)
    filePath = getPersonalSubPathFile(subDir, fileName)
    remotePath = repoUrl
    subDir = subDir.lower()

    if sameRemoteSub:
        remotePath = f"{repoUrl}/{subDir}"
    forceDownload = serverFileNeedsUpdate(subDir, fileName, remotePath, checkServerFileTimeStamp, onceaday)

    if not forceDownload:
        try:
            fileContent = readFile(filePath)
        except:
            fileContent = ""

    if not fileContent or forceDownload:
        url = f"{remotePath}/{fileName}"
        fileContent, s = downloadFile(url, filePath, True)

    return fileContent


def readLocalOrGetOnLineFileContent(urlOrPath, subDir, fileName, forceGetOnLine = False, defaultContent = ""):
    fileContent = ""
    createSubDir(subDir)
    filePath = getPersonalSubPathFile(subDir, fileName)
    subDir = subDir.lower()

    forceDownload = forceGetOnLine
    if not forceDownload:
        forceDownload = not os.path.isfile(filePath)

    if not forceDownload:
        try:
            fileContent = readFile(filePath)
        except:
            fileContent = ""

    forceDownload = fileContent == ""

    if forceDownload:
        try:
            if isAvailable(urlOrPath):
                parsed_url = urllib.parse.urlparse(urlOrPath)
                if parsed_url.scheme in ['http', 'https']:
                    fileContent_tmp, s = downloadFile(urlOrPath, filePath, True)
                elif parsed_url.scheme == 'ftp':
                    fileContent_tmp = downloadFtpFile(urlOrPath, "", "", filePath, True)
                else:
                    fileContent_tmp = readFile(urlOrPath)
                    writeFile(filePath, fileContent_tmp)

                if fileContent_tmp:
                    fileContent = fileContent_tmp
            else:
                logger.error("Cannot get/download/update file: '{fileName}'")
                # if not MessageBoxQuestion(f"Cannot get/download/update file: '{fileName}', retry later?"):
                #     fileContent = fileContent or defaultContent
                #     writeFile(filePath, fileContent)
        except Exception as e:
            logger.error(f"downloadFile error {fileName}")
            logger.error(e)
            pass

    return fileContent


def isExpiredFile(filePath, expirationDays=1):
    last_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filePath)).date()
    today = datetime.datetime.now().date()

    if expirationDays>0:
        today = last_modified_date + datetime.timedelta(days=expirationDays)

    return today > last_modified_date


def decodeJwt(token):
    payload = None

    try:
        parts = token.split('.')
		
        if len(parts) != 3:
            logger.info("Invalid Token")
            return None  # Token non valido

        _payload = parts[1]
        _payload += '=' * (4 - (len(_payload) % 4) if len(_payload) % 4 else 0)  

        payload = json.loads(base64.b64decode(_payload).decode('utf-8'))
    except Exception as e:
        logger.error(f"Error during b64decode: [{e}]")
        pass
        
    return payload


def isJwtExpired(token):
    payload = decodeJwt(token)

    if not payload:
        return True  # Token non valido
    
    exp = payload.get("exp")
    if exp is None:
        return False  # Il token non ha scadenza definita, quindi presumibilmente e' valido
    
    return time.time() > exp


def serverFileNeedsUpdate(subDir, fileName, remotePath, checkServerFileTimeStamp=False, onceaday=True):
    res = False
    if not checkServerOnLine():
        return res

    filePath = getPersonalSubPathFile(subDir, fileName)

    logger.debug(f"Check update for File: {subDir}/{fileName}, FromServer: {checkServerFileTimeStamp}, Once a Day: {onceaday}")
    if not checkFileExists(filePath):
        logger.info(f"Cannot get localfile {subDir}/{fileName}, needs update")
        res = True
    else:
        try:
            if checkServerFileTimeStamp:
                last_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filePath))
                day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][last_modified_date.weekday()]

                if onceaday:
                    modified_since = last_modified_date.strftime("%d %b %Y 23:59:59 GMT")  # once a day it's enought
                else:
                    modified_since = last_modified_date.strftime("%d %b %Y %H:%M:%S GMT")

                url = f"{remotePath}/{fileName}"
                req = requests.get(url,headers={"If-Modified-Since": f"{day}, {modified_since}"}, timeout=5)
                status = req.status_code
                
                # etag = "xxxxxxxxxxx"
                # req = requests.get(url,headers={"If-None-Match": f'"{etag}"'}, timeout=5)
                # status = req.status_code

                #if status == 404:  # not found on server
                #    res = False
                #elif (req.status_code != 304):  # cannot read from local file because of CACHE, needs update
                #    res = True

                if status == 200:  # OK .. it's modified, needs update
                    res = True
                logger.debug(f"Query status code: {req.status_code} is changed: {res}")
            else:
                dt = datetime.datetime.now()
                file_datetime = datetime.datetime.fromtimestamp(os.path.getctime(filePath))
                res = (dt - file_datetime).days > 1
        except OSError as e:
            if "HTTPConnectionPool" in str(e):
                logger.error(f"Error getting remote file info {fileName}, cannot check update", e)
                res = False
            else:
                logger.error(f"Error getting local file info {fileName}, needs update", e)
                res = True
        except Exception as e:
            logger.error(f"Error during serverFileNeedsUpdate check: [{e}]")
            logger.error(f"Force download {fileName}")
            res = True

    return res


def localFileNeedsUpdate(filePath, expiringDays = -999, minSize = 0):
    res = True

    if checkFileExists(filePath):
        fileSize = os.path.getsize(filePath)
        if fileSize < minSize:
            expiringDays = -1

        if expiringDays == -999:
            expiringDays = EXPIRING_LOCAL_FILES_DAYS
        fileExpiredDate = datetime.datetime.fromtimestamp(os.path.getmtime(filePath)) + datetime.timedelta(days=expiringDays)
        dtExpFile = int(fileExpiredDate.strftime("%Y%m%d"))
        dtNow = int(datetime.date.today().strftime("%Y%m%d"))
        res = dtNow >= dtExpFile

    return res


def checkForUpdates():
    getOrUpdateEpg()

    logger.debug("starts...")
    res = False

    # if directory ADDONUSERPATH doesn't exist (first launch after installation)
    # I create it manually to get first Updates if needs
    isExistAddonDirectory = checkFileExists(translatePath(config.ADDON_USER_PATH))
    if not isExistAddonDirectory:
        os.makedirs(translatePath(config.ADDON_USER_PATH))

    if config.isDEV():
        MessageNotification("DEV MODE! check disabled", 1)
        return

    itsTimeToCheck = False
    fileTimer = getPersonalPathFile(LAST_CHK_INF)

    if checkFileExists(fileTimer):
        t = time.time() - os.path.getmtime(fileTimer)
        if t > 3600: # check every hour
            itsTimeToCheck = True
    else:
        itsTimeToCheck = True

    logger.debug("itsTimeToCheck: ", itsTimeToCheck)
    if itsTimeToCheck:
        try:
            res = installUpdates()
        except:
            pass

        writeFile(fileTimer, str(datetime.datetime.fromtimestamp(time.time())))

    return res


def getCurrentVersionAndHotfix():
    hotfixLocalNumber = 0
    vers=config.ADDON_VERSION.split("~")

    versInt=vers[0]
    versStr=""

    if len(vers) == 1:
        addonVersionNumber = int(versInt.replace(".", ""))
        localHotfixInfoFile = getPersonalPathFile(HOTFIX_FILE_INFO)

        if os.path.isfile(localHotfixInfoFile):
            hotfixLocalJson = json.loads(readFile(localHotfixInfoFile))
            verLocalNumber = int(hotfixLocalJson["version"].replace(".", ""))

            if verLocalNumber >= addonVersionNumber:
                hotfixLocalNumber = hotfixLocalJson["hotfix"]
    else:
        versStr=vers[1]

    return config.ADDON_VERSION, hotfixLocalNumber


def getCurrentVersionAndHotfixString():
    vers, hotfix = getCurrentVersionAndHotfix()

    version_string = str(vers)
    if hotfix != "0" and hotfix != 0:
        version_string = f"{version_string} (hotfix:{hotfix})"

    strMsg = config.ADDON.getLocalizedString(30134)
    strMsg = strMsg.format(version_string)
    return strMsg


def getGuid(strInput):
    return scrapers.findSingleMatch(strInput.lower(), r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}')

def isGuid(strInput):
    """Controlla se una stringa ha il formato di un UUID usando una regex."""
    return len(getGuid(strInput))>0

def getApikeyParameter():
    admin_token = getAdminToken()
    if not admin_token:
        admin_token = ""
    else:
        admin_token = f"apikey={admin_token}&"

    return admin_token


def getAdminToken():
    FILE = translatePath(os.path.join(config.ADDON_PATH, "admin_token"))
    if os.path.isfile(FILE):
        token = readFile(FILE)
        logger.info(f"we found an \"admin_token\" file. Try to use: {token}")
        return token

    if config.isBeta():
        return BETA_TOKEN
    else:
        return None


def getRandomID(lenght:int)->str:
    uId = str(uuid.uuid4()).replace("-", "")
    if lenght > len(uId):
        return uId
    else:
        return uId[:lenght]


def installUpdates():
    res = False
    verServerString = ""
    verServerNumber = 0
    hotfixServerNumber = 0
    hotfixFileServer = ""
    verLocalNumber = 0
    hotfixLocalNumber = 0
    updateDescription = ""

    url = f"{ADDON_REPO_HOTFIX}/{HOTFIX_FILE_INFO}"
    localHotfixInfoFile = getPersonalPathFile(HOTFIX_FILE_INFO)

    try:
        hotfixServerJson = requests.get(url).json()

        for hotfixServer in hotfixServerJson:
            verServerString = hotfixServer["version"]
            verDestination = hotfixServer["destination"]
            if verDestination == config.ADDON_VERSION:
                verServerNumber = int(verServerString.replace(".", ""))
                hotfixFileServer = hotfixServer["filename"]
                typeofupdate = hotfixServer["type"]
                hotfixServerNumber = hotfixServer["hotfix"]
                updateDescription = hotfixServer["description"]
                break

        if os.path.isfile(localHotfixInfoFile):
            hotfixLocalJson = json.loads(readFile(localHotfixInfoFile))
            verLocalNumber = int(hotfixLocalJson["version"].replace(".", ""))
            hotfixLocalNumber = hotfixLocalJson["hotfix"]
    except:
        pass  # local json do not exists, I keep default values

    updateAvailable = (verServerNumber > verLocalNumber) or (verServerNumber == verLocalNumber and hotfixServerNumber > hotfixLocalNumber)

    if updateAvailable:
        dataFile = getPersonalPathFile(HOTFIX_FILE)
        logger.info(f"A new {typeofupdate} update (v.{verServerString}.{hotfixServerNumber}) is available, download and install...")
        if os.path.isfile(dataFile):
            os.remove(dataFile)

        url = f"{ADDON_REPO_HOTFIX}/{hotfixFileServer}"
        downloadFile(url, dataFile)

        xbmc.executebuiltin(f"Extract({dataFile}, {config.ADDON_ROOT_PATH})")
        xbmc.executebuiltin("UpdateLocalAddons")

        xbmc.sleep(1500)

        writeFile(localHotfixInfoFile, str(json.dumps(hotfixServer)))
        writeFile(dataFile, "update applied")

        strmsg = config.ADDON.getLocalizedString(30133)
        strmsg = strmsg.format(typeofupdate, verServerString, hotfixServerNumber)
        logger.info(strmsg)
        strmsg = f"{strmsg}\n\n{updateDescription}"

        xbmcgui.Dialog().ok(ADDON_NAME, strmsg)
        res = True
    else:
        logger.debug("No updates available, exit.")

    return res


def forceCheckUpdate(forceHotfix=False):
    logger.debug("Force check update")
    dir = translatePath(config.ADDON_USER_PATH)
    file = os.path.join(dir, LAST_CHK_INF)
    if os.path.isfile(file):
        os.remove(file)

    if forceHotfix:
        logger.debug("Force hotfix is true")
        file = os.path.join(dir, HOTFIX_FILE_INFO)
        if os.path.isfile(file):
            os.remove(file)

    res = checkForUpdates()
    if not res:
        xbmc.executebuiltin("Notification({}, {}, {})".format(ADDON_NAME, "No hotfix available", 4000))


def getWidevineVersion():
    rc = "" # 4.10.2891.0 ==> issued

    if xbmc.getCondVisibility('system.platform.android'):
        return rc

    try:
        is_addon = xbmcaddon.Addon('inputstream.adaptive')
        is_version = is_addon.getAddonInfo('version')
    except:
        return rc
    
    try:
        cdm_path = is_addon.getSetting('DECRYPTERPATH')
        if not cdm_path:
            for setting_name in ['CDMPATH', 'DRM_PATH']:
                cdm_path = is_addon.getSetting(setting_name)
                if cdm_path:
                    break
        
        cdm_path = translatePath(cdm_path)
        
        manifest_path = os.path.join(cdm_path, 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                rc = manifest.get("version", "")

    except Exception as e:
        return rc

    return rc


def cacheCleanup(files=""):
    logger.debug("Start cache file cleanup")

    if files:
        cleanupFiles(files)
    else:
        cleanupFiles("*.bin,*.dat,*.lst,~*")

    logger.debug("Cache file cleanup completed")
    xbmc.executebuiltin("Notification({}, {}, {})".format(ADDON_NAME, "Cache files has been cleanup!", 4000))


def cleanupFiles(searchPattern: str):
    if not searchPattern:
        return

    logger.debug(f"Start file cleanup: {searchPattern}")
    userFiles = getFiles(searchPattern=searchPattern)

    for filename in userFiles:
        if os.path.isfile(filename):
            logger.debug("Delete: ", filename)
            xbmcvfs.delete(filename)

    logger.debug("File cleanup completed")


def getContentResource(fileName, subDir = "", sameRemoteSubDir = False):
    fileContent = readLocalOrDownload(FILE_REPO_URL, subDir, fileName, sameRemoteSubDir)
    decomp = ""
    try:
        decomp = zlib.decompress(base64.b64decode(fileContent), -15)
    except Exception as e:
        logger.error("Error decompressing files: ", e)

    return decomp

def decompressString(input, encoding="ascii"): # "ascii", "utf8"
    """
        ** decompress **

        Decompress a Base64 string

        :param encoding: encoding string like "ascii" or "utf8"

        Example::
            ..
            string = decompressString(compressed_base64_string, "ascii")
            ..
    """
    string = ""
    if input:
        try:
            string = zlib.decompress(base64.b64decode(input.encode(encoding))).decode(encoding)
        except Exception as e:
            logger.error("Error decompressing: ", e)

    return string

def compressString(input, encoding="ascii"):   # "ascii", "utf8"
    """
        ** compress **

        Compress a string into Base64 string

        :param encoding: encoding string like "ascii" or "utf8"

        Example::
            ..
            string = compressString(plain_text_string, "ascii")
            ..
    """
    string = ""
    if input:
        try:
            string = base64.b64encode(zlib.compress(input.encode(encoding), 9)).decode(encoding)
        except Exception as e:
            logger.error("Error compressing: ", e)

    return string


def toBase64(input, encoding="utf8"):
    return base64.b64encode(input.encode(encoding)).decode(encoding)

def fromBase64(input, encoding="utf8"):
    return base64.b64decode(input.encode(encoding)).decode(encoding)


def getFileFullPath(fileName, subDir = ""):
    return translatePath(os.path.join(config.ADDON_USER_PATH, subDir, fileName))


def getRemoteLists() -> List[CustomList]:
    res = list()
    jsonLists = list()
    jsonListsEL  = getEmergencyDTTFtaList()

    fileFullName = getFileFullPath("lists.bin")

    if checkServerOnLine():
        try:
            jsonLists = apiRequester("/all.json")
            if localFileNeedsUpdate(fileFullName):
                writeFile(fileFullName, json.dumps(jsonLists))
        except Exception as ex:
            logger.error("Error during get online available lists")
            logger.error(ex)
    else: #try locally
        try:
            for item in jsonListsEL: jsonLists.append(item)
            jsonListsLCL = json.loads(readFile(fileFullName))
            for item in jsonListsLCL:
                if not item.get("DisplayName",""): item["DisplayName"] = item["Name"]
                item["DisplayName"] = item["DisplayName"] + " (cached)"
                jsonLists.append(item)
        except Exception as ex:
            logger.error("Error during get local available lists")
            logger.error(ex)

    for item in jsonLists:
        m3u = M3UList.from_dict(item)
        m3u.Id = m3u.Name
        custom = CustomList(m3u.Id, m3u.DisplayName, ListType.Official, [m3u])
        isOfficial2Add = (m3u.Enabled or config.isDEV() or config.isBeta()) and TAG_ADDON_KODILIST in m3u.Tags

        if m3u.IsEmergency:
            custom.TypeOfList = ListType.Emergency

        if m3u.IsEmergency or isOfficial2Add:
            res.append(custom)

        if isOfficial2Add:
            cacheFilesIfNeeds(custom)

    return res


def cacheFilesIfNeeds(customLists):
    getOnlineOrLocalCacheLink(computeListUrl(customLists))


def getRemoteGroups() -> List[M3UList]:
    res = list()
    jsonLists = list()
    fileFullName = getFileFullPath("groups.bin")

    if checkServerOnLine():
        try:
            jsonLists = apiRequester("/all/groups.json")

            if(localFileNeedsUpdate(fileFullName)):
                writeFile(fileFullName, json.dumps(jsonLists))
        except Exception as ex:
            logger.error("Error during get online available groups")
            logger.error(ex)
    else:
        try:
            jsonLists = json.loads(readFile(fileFullName))
        except Exception as ex:
            logger.error("Error during get local available groups")
            logger.error(ex)

    for item in jsonLists:
        m3u = M3UList.from_dict(item)
        m3u.Id = m3u.Name

        isOfficial2Add = (m3u.Enabled or config.isDEV() or config.isBeta()) and TAG_ADDON_KODILIST in m3u.Tags

        if isOfficial2Add:
            res.append(m3u)
    return res


def getEmergencyDTTFtaList():
    #dttFtaPath = translatePath(os.path.join(config.ADDON_PATH, "resources", EMR_LIST_FILE))
    return [{"Name": "Emergency", "DisplayName": "DTT FTA (Emergenza)", "List": getOrUpdateEmergencyList(), "Epg": getOrUpdateEpg(), "IsEmergency": True, "IsUserList": False, "IsValid": True}]


def getEmptyList() -> M3UList:
    emptyPath = translatePath(os.path.join(config.ADDON_PATH, "resources", EMPTY_FILE))
    emptyEpg = translatePath(os.path.join(config.ADDON_PATH, "resources", EMPTY_EPG_FILE_NAME))
    return M3UList.from_dict({"Name": "Empty", "DisplayName": "Empty", "List": emptyPath , "Epg": emptyEpg, "IsEmergency": False, "IsUserList": False, "IsValid": True})


def getUserAgentForLink(url):
    return f"{url}|User-Agent={const.USER_AGENT}"


def checkSettings():
    if config.isBeta():
        config.setSetting("isBeta", True)

    selected = config.getSetting(const.SELECTED_LIST)
    lastSelected = config.getSetting(const.LAST_SELECTED_ONLINE_LIST)

    if lastSelected and selected != lastSelected and checkServerOnLine():
        if MessageBoxQuestion(30182):
            remoteLists = getRemoteLists()
            selectedList = next( iter( filter( lambda c: (c.Id == lastSelected), remoteLists ) ) )
            m3uList = selectedList.Lists[0]
            m3uList.List = getOnlineOrLocalCacheLink(computeListUrl(selectedList))
            m3uList.Epg = getOrUpdateEpg()

            setList(m3uList)

    return


def checkSetup():
    kodiVersion = getInstalledVersion()
    logger.info(f"Kodi version detected is: {kodiVersion}, minimum is {UNSUPPORTED_KODI_VERSION}")
    logger.info(f"Python version: {sys.version}, API: {sys.api_version}")

    if kodiVersion <= UNSUPPORTED_KODI_VERSION:
        logger.error("Kodi version unsuported")
        MessageBox(30192)
        return False

    check = install.isOfficiallyInstalled()
    if not check:
        logger.error("Not officially installed")
        MessageBox(30190)
        return False

    return True


def computeListUrl(selectedList: CustomList) -> str:
    link = ""
    apiKeyParameter = getApikeyParameter()

    if len(selectedList.Lists) == 1 and selectedList.TypeOfList == ListType.Official:
        # user has selected a full list
        selected = selectedList.Lists[0]
        link = f"{API_DOMAIN}/{selected.Id}/list.m3u8?{apiKeyParameter}"
    else:
        # user has selected a personal list
        selectedGroups = []
        for selected in selectedList.Lists:
            selectedGroups.append("{}={}".format(selected.Id, ",".join(selected.Groups)))
        link = "{}/all/groups/merge.m3u8?{}{}".format(API_DOMAIN, apiKeyParameter, "&".join(selectedGroups))

    return link


def getOnlineOrLocalCacheLink(url):
    fileFullName = getFileFullPath("{}.lst".format(hashlib.md5(url.encode('utf8')).hexdigest()))

    if checkServerOnLine():
        try:
            if localFileNeedsUpdate(fileFullName):
                request.urlretrieve(url, fileFullName)
        except Exception as ex:
            logger.error(f"Error during get file: {fileFullName} from online m3u: {url}")
            logger.error(ex)
    else: #try locally
        url = fileFullName

    return url


def refreshFileDate(input):
    if checkFileExists(input):
        _tmpFile = getPersonalPathFile("~tmp")
        xbmcvfs.copy(input, _tmpFile)
        xbmcvfs.delete(input)
        xbmcvfs.copy(_tmpFile, input)
        xbmcvfs.delete(_tmpFile)

    return True


def checkFileExists(input):
    return xbmcvfs.exists(input)


def checkUrlExists(input, timeout = 30):
    res = False
    status_code = 0

    parsed_url = urllib.parse.urlparse(input)
    url2check = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        headers = {"user-agent": const.USER_AGENT}
        status_code = requests.head(url2check, headers = headers, timeout = timeout).status_code
        if status_code == 405:
            raise Exception("Method head not allowed")
        res = status_code == 200
    except requests.Timeout:
        pass
    except Exception as ex:
        if status_code != 405:
            logger.error(ex)
        try:
            res = requests.get(url2check, headers = headers, timeout = timeout).status_code == 200
        except Exception as ex:
            logger.error(ex)

    return res


def isHttpAvailable(url, checkType = 0, timeout = 1):
    rc = False
    status_code = 0

    headers = {"user-agent": const.USER_AGENT}

    parsed_url = urllib.parse.urlparse(url)
    url2check = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        if checkType == 0:
            rc, status_code = isHttpAvailable(url2check, 1)
            if not rc:
                rc, status_code = isHttpAvailable(url2check, 2)
            if not rc:
                rc, status_code = isHttpAvailable(url2check, 3)
            if not rc:
                rc, status_code = isHttpAvailable(url2check, 4)
        elif checkType == 1:
            res = requests.head(url2check, timeout=timeout)
            status_code = res.status_code # status_code == 405 => "Method head not allowed"
            if status_code == 200:
                res.close()
                rc = True
        elif checkType == 2:
            res = requests.options(url2check, timeout=timeout)
            if status_code == 200:
                res.close()
                rc = True
        elif checkType == 3:
            res = requests.get(url2check, stream=True, timeout=timeout)
            if status_code == 200:
                res.close()
                rc = True
        elif checkType == 4:
            port = 443 if parsed_url.scheme == 'https' else 80
            with socket.create_connection((parsed_url.hostname, port), timeout=timeout):
                status_code = 200
                rc = True
    except requests.RequestException as rex:
        logger.error(rex)
        pass
    except Exception as ex:
        logger.error(ex)
        pass

    return rc, status_code

def isFtpAvailable(url, timeout = 10):
    from ftplib import FTP
    parsed_url = urllib.parse.urlparse(url)

    try:
        ftp = FTP(parsed_url.hostname, timeout=timeout)
        ftp_user = parsed_url.username or "anonymous"  # Default "anonymous" if not specified
        ftp_password = parsed_url.password or ""

        ftp.login(ftp_user, ftp_password)
        ftp.cwd(os.path.dirname(parsed_url.path))

        if os.path.basename(parsed_url.path) in ftp.nlst():
            ftp.quit()
            return True
    except requests.RequestException as rex:
        logger.error(rex)
        pass
    except Exception as ex:
        logger.error(ex)
        pass

    return False

def isAvailable(value, timeout = 2):
    rc = False
    status_code = 0

    parsed_url = urllib.parse.urlparse(value)
    if parsed_url.scheme in ['http', 'https']:
        if timeout == 0:
            rc, status_code = isHttpAvailable(value, 3)
        else:
            rc, status_code = isHttpAvailable(value)
    elif parsed_url.scheme == 'ftp':
        rc = isFtpAvailable(value, timeout)
    else:
        rc = xbmcvfs.exists(value) and os.path.isfile(value) #os.access(value, os.R_OK)

    return rc


def getInstalledVersion():
    kodiVersionInstalled = 0
    # retrieve kodi installed version
    #jsonProperties = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    jsonProperties = jsonrpcRequest("Application.GetProperties", {"properties": ["version", "name"]})
    #jsonProperties = unicode(jsonProperties, 'utf-8', errors='ignore')

    #if jsonProperties.has_key('result') and jsonProperties['result'].has_key('version'):
    kodiVersionInstalled = int(jsonProperties['result']['version']['major'])

    return kodiVersionInstalled


def getPvrSimpleInstancesSettings():
    pvrSimpleInstances = []

    simpleClient = xbmcaddon.Addon(install.ADDON_ID_PVR)
    pvrPath = simpleClient.getAddonInfo("profile")

    instancesSettingsFiles = getFiles(pvrPath, "instance-settings*.xml")

    for file in instancesSettingsFiles:
        filename = os.path.basename(file)
        instanceId = scrapers.findSingleMatch(filename, r"\d")

        # instanceName = simpleClient.getSetting("kodi_addon_instance_name", instanceId) #not yet implemented in kodi
        # enabled = simpleClient.getSetting("kodi_addon_instance_enabled", instanceId)   #not yet implemented in kodi
        instanceName = getSettingValueFromXml("kodi_addon_instance_name", file)
        enabled = getSettingValueFromXml("kodi_addon_instance_enabled", file)

        epg = getSettingValueFromXml("epgPath", file)
        m3u = getSettingValueFromXml("m3uUrl", file)

        instance = { "name" : instanceName , "instanceId": instanceId, "enabled": enabled, "epg": epg, "m3u": m3u }
        pvrSimpleInstances.append(instance)

    return pvrSimpleInstances


def getSettingValueFromXml(settingName, file):
    from lib import xmltodict
    xml = xmltodict.parse(readFile(file))
    data = xml["settings"]

    id2text = {}

    for setting in data["setting"]:
        setting_id = setting["@id"]
        setting_text = setting.get("#text")  # Usa get per ottenere il valore, restituisce None se la chiave non esiste
        if not setting_text: setting_text = ""

        id2text[setting_id] = setting_text

    return id2text[settingName]


def addonEnable(addonId, enabled):
    jsonrpcRequest("Addons.SetAddonEnabled", { "addonid": addonId, "enabled": enabled })


def reloadProfile():
    xbmc.executebuiltin('LoadProfile(Master user)')


def jsonrpcRequest(method, params=None):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params if params else {},
        "id": 1
    }

    response = xbmc.executeJSONRPC(json.dumps(request))
    return json.loads(response)


def setList(m3u: M3UList, isOffline: bool = False):
    isSimpleInstalled = install.installPvr()

    if isSimpleInstalled:
        simpleClient = xbmcaddon.Addon(install.ADDON_ID_PVR)

        pvrSimpleInstances = getPvrSimpleInstancesSettings()
        #addonEnable(install.ADDON_ID_PVR, False)

        wltvItem = next((item for item in pvrSimpleInstances if item['name'] == 'WLTV'), None)

        if not wltvItem:
            instanceId = 1
        else:
            instanceId = wltvItem['instanceId']

        pvrPath = simpleClient.getAddonInfo("profile")
        settingsFilePath = os.path.join(pvrPath, "settings.xml")
        settingsInstanceFilePath = os.path.join(pvrPath, f"instance-settings-{instanceId}.xml")

        settingsFilePath = translatePath(settingsFilePath)
        settingsInstanceFilePath = translatePath(settingsInstanceFilePath)

        simpleClient.setSetting("m3uPathType", "1")
        simpleClient.setSetting("epgPathType", "0")
        #simpleClient.setSetting("epgCache", False)

        epgEnabled = config.getSetting("enable_epg")

        if m3u.Epg:
            if not epgEnabled:
                simpleClient.setSetting("epgPath", "")
            else:
                simpleClient.setSetting("logoFromEpg", "2")
                simpleClient.setSetting("epgPath", m3u.Epg)
        else:
            simpleClient.setSetting("epgPath", "")
            simpleClient.setSetting("logoFromEpg", "0")

        simpleClient.setSetting("m3uUrl", m3u.List)

        simpleClient.setSetting("kodi_addon_instance_name", "WLTV")
        simpleClient.setSetting("kodi_addon_instance_enabled", "true")
        xbmcvfs.copy(settingsFilePath, settingsInstanceFilePath)
        xbmcvfs.delete(settingsFilePath)

        m3uId = f"{m3u.Id}_offline" if isOffline else m3u.Id
        config.setSetting(const.SELECTED_LIST, m3uId) #Set selected list in settings

        # show a simple notification informing user new IPTV list has been set
        MessageNotification(config.getString(30120).format(m3u.DisplayName))

        cleanupPvrCache()
        # xbmc.sleep(1000)
        # addonEnable(install.ADDON_ID_PVR, True)


def cleanupPvrCache():
    logger.info("Cleaning up PVR cache...")
    from lib.dal import DAL

    simpleClient = xbmcaddon.Addon(install.ADDON_ID_PVR)
    addonEnable(install.ADDON_ID_PVR, False)
    xbmc.sleep(1500)

    pvrPath = simpleClient.getAddonInfo("profile")
    userFiles = getFiles(pvrPath, "iptv.m3u.cache*,xmltv.xml.cache*")

    for filename in userFiles:
        if os.path.isfile(filename): xbmcvfs.delete(filename)

    fileTV = getFiles("special://database", "TV*.db")
    fileEpg = getFiles("special://database", "Epg*.db")

    fileTV.sort()
    fileEpg.sort()

    if len(fileTV) > 1 or len(fileEpg) > 1:
        logger.error("More db TV or Epg files into directory!!! Last will be chosen...")

    dbfilePathTV = fileTV[-1]
    dbfilePathEpg = fileEpg[-1]

    logger.info(f"Using db file for TV: {dbfilePathTV}")
    logger.info(f"Using db file for EPG: {dbfilePathEpg}")
    
    db = DAL(dbfilePathEpg)
    db.connect()

    res = db.delete("lastepgscan")
    if res:
        logger.info("Deleted last epg scan")
    res = db.delete("epgtags")
    if res:
        logger.info("Deleted epgtags")
    
    res = db.delete("epg")
    if res:
        logger.info("Deleted epg")
    db.close()

    db = DAL(dbfilePathTV)
    db.connect()
    res = db.update("channels", "idEpg = null")
    if res:
        logger.info("Updated channels")
    db.close()

    xbmc.sleep(500)
    addonEnable(install.ADDON_ID_PVR, True)


def getSelectedList() -> M3UList:
    addonEnable(install.ADDON_ID_PVR, True)
    pvrSimpleInstances = getPvrSimpleInstancesSettings()

    wltvItem = next((item for item in pvrSimpleInstances if item['name'] == 'WLTV'), None)

    if not wltvItem:
        MessageBox("WLTV Instance not found")
        return

    instanceId = wltvItem['instanceId']
    m3u = wltvItem["m3u"]
    epg = wltvItem["epg"]
    lastSelectedId = config.getSetting(const.LAST_SELECTED_ONLINE_LIST)

    return M3UList.from_dict({"Id": lastSelectedId, "Name": "Empty", "DisplayName": "Empty", "List": m3u , "Epg": epg, "IsEmergency": False, "IsUserList": False, "IsValid": True})


def reloadEPG():
    progress = xbmcgui.DialogProgress()
    progress.create(config.getString(30194), config.getString(30195)) #Reloading EPG, please wait...

    # Step 1
    progress.update(10, config.getString(30196)) #EPG Downloading...
    epgPath, isBanned, needsEpgUpdate = getOrUpdateEpgResult()
    progress.update(50, config.getString(30200)) #completed

    # Step 2
    progress.update(51, config.getString(30197)) #Channel list cleaning...
    cleanupPvrCache()
    progress.update(100, config.getString(30200)) #complete

    # Close the progress bar dialog
    progress.close()

    MessageNotification(config.getString(30199)) #EPG reload done

    if isBanned:
        MessageBox(30193)
        #MessageNotification(30193, 5)


def setListInt(listName, m3uListUrl, epgUrl):
    m3u = M3UList()
    m3u.Name = listName
    m3u.List = m3uListUrl
    m3u.Epg = epgUrl
    setList(m3u)


def addMenuItem(handle, title, url, imagedir = "", icon = "", thumb = "", poster = "", fanart = "", isFolder = True):
    if imagedir == "":
        imagedir = "images"

    if isinstance(title, int):
        title = config.getString(title)

    li = xbmcgui.ListItem(title)

    _icon   = f"{icon}.png" if icon else ""
    _thumb  = f"{thumb}.png" if thumb else _icon
    _poster = f"{poster}.png" if poster else _thumb
    _fanart = f"{fanart}.png" if fanart else "wltv-background.png"

    li.setArt(
        {
            "icon"  : os.path.join(config.ADDON_PATH, "resources", imagedir, _icon  ) if _icon   else None,
            "thumb" : os.path.join(config.ADDON_PATH, "resources", imagedir, _thumb ) if _thumb  else None,
            "poster": os.path.join(config.ADDON_PATH, "resources", imagedir, _poster) if _poster else None,
            "fanart": os.path.join(config.ADDON_PATH, "resources", imagedir, _fanart) if _fanart else None,
        }
    )

    xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=isFolder)


def addMenuItemVideoM3U(handle, item: M3UItem):
    link = item.Link
    params = dict()
    if item.UserAgent:
        params["user-agent"]=item.UserAgent
    if item.Referer:
        params["referer"]=item.Referer
    if params:
        link = f"{item.Link}|{urlencode(params)}"
    return addMenuItemVideo(handle, item.Title, link, "", item.TvgLogo, isFolder=False)


def addMenuItemAudio(handle, title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", isFolder=False):
    addMenuItemPlayable(handle, title, url, plot, icon, thumb, poster, fanart, genre, year, mediatype="audio", isFolder=isFolder)


def addMenuItemVideo(handle, title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", isFolder=False):
    addMenuItemPlayable(handle, title, url, plot, icon, thumb, poster, fanart, genre, year, mediatype="video", isFolder=isFolder)


def addMenuItemPlayable(handle, title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", mediatype="", isFolder=True):
    if isinstance(title, int):
        title = config.getString(title)

    li = xbmcgui.ListItem(title)

    #plot          string (Long Description)
    #plotoutline   string (Short Description)
    #title         string (Big Fan)
    #originaltitle string (Big Fan)
    #sorttitle     string (Big Fan)
    #title = title + "[CR]----"

    if not isFolder:
        li.setProperty("IsPlayable", "true")

    li.setInfo("video", {"title": title, "plot": plot, "plotoutline": plot, "genre": genre, "year": year, "mediatype": mediatype})

    li.setArt(
        {
            "icon":   icon,
            "thumb":  thumb  if thumb  else icon,
            "poster": poster if poster else icon,
            "fanart": fanart if fanart else icon,
        }
    )

    xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=isFolder)


def getListItem(title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", mediatype="", isFolder=True):
    if isinstance(title, int):
        title = config.getString(title)

    li = xbmcgui.ListItem(title)

    if not isFolder:
        li.setProperty("IsPlayable", "true")

    li.setInfo("video", {"title": title, "plot": plot, "plotoutline": plot, "genre": genre, "year": year, "mediatype": mediatype})

    li.setPath(url)
    li.setArt(
        {
            "icon":   icon,
            "thumb":  thumb  if thumb  else icon,
            "poster": poster if poster else icon,
            "fanart": fanart if fanart else icon,
        }
    )
    return li


def createPlayableMediaListItemsMenu(handle, name: str, showPosters: bool, listItems: List[PlayableMediaItem]):
    xbmcplugin.setPluginCategory(handle, name)
    xbmcplugin.setContent(handle, "videos")

    seasons = set(list(map(lambda item: item.Season, listItems)))
    name = listItems[0].Title

    for s in seasons:
        if len(seasons) > 1:
            addMenuItem(handle, f"======== Season {str(s).zfill(2)} - {name} ========", "")

        episodes = list(filter(lambda item: item.Season == s, listItems))

        for item in episodes:
            thumb  = item.Thumbnail
            logo   = item.Fanart
            fanart = item.Fanart
            poster = item.Fanart
            isFolder = item.IsExternalLink #False

            if not showPosters:
                thumb  = ""
                logo   = "movie.png" if item.IsFilm else "tvshow.png"
                logo   = os.path.join(config.ADDON_PATH, "resources", logo)
                fanart = ""
                poster = ""

            addMenuItemVideo(handle, title=item.GetTitle(), url=item.Link, plot=item.Plot, icon=logo, thumb=thumb, poster=poster, fanart=fanart, genre=(), year="", isFolder=isFolder)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle)


def getBroadcaster(broadcaster, showmessage = True):
    c = importlib.util.find_spec(f"broadcaster.{broadcaster}")
    found = c is not None
    if found:
        try:
            c = importlib.import_module(f"broadcaster.{broadcaster}")
        except Exception as ex:
            logger.error(f"Error: [{ex}]")
    else:
        c = None
        msg = f"Sorry, broadcaster '{broadcaster}' not found"
        logger.debug(msg)
        if showmessage:
            MessageBox(msg)

    return c


def vttToSrt(data):
    import re
    # Code adapted by VTT_TO_SRT.PY (c) Jansen A. Simanullang
    ret = ''

    data = re.sub(r'(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', data)
    data = re.sub(r'(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'00:\1,\2 --> 00:\3,\4\n', data)
    data = re.sub(r'(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'00:00:\1,\2 --> 00:00:\3,\4\n', data)
    data = re.sub(r'WEBVTT\n', '', data)
    data = re.sub(r'Kind:[ \-\w]+\n', '', data)
    data = re.sub(r'Language:[ \-\w]+\n', '', data)
    data = re.sub(r'<c[.\w\d]*>', '', data)
    data = re.sub(r'</c>', '', data)
    data = re.sub(r'<\d\d:\d\d:\d\d.\d\d\d>', '', data)
    data = re.sub(r'::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n', '', data)
    data = re.sub(r'Style:\n##\n', '', data)

    lines = data.split(os.linesep)

    for n, line in enumerate(lines):
        if re.match(r"((\d\d:){2}\d\d),(\d{3}) --> ((\d\d:){2}\d\d),(\d{3})", line):
            ret += str(n + 1) + os.linesep + line + os.linesep
        else:
            ret += line + os.linesep

    return ret
