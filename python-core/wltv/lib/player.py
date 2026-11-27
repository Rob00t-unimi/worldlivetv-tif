# -*- coding: utf-8 -*-

import xbmcgui
import xbmc
import xbmcplugin
import routing
import importlib

from urllib.parse import urlencode

from lib.broadcaster_result import BroadcasterResult
from lib.install import getInputStreamAdaptiveVersion, installInputStreamAdaptive, installWidevine
from lib import const, logger, config, utils

plugin = routing.Plugin()


def play(broadcaster, channel):
    # import broadcaster and start playing
    res = None

    c = importlib.util.find_spec(f"broadcaster.{broadcaster}")
    found = c is not None
    if found:
        c = importlib.import_module(f"broadcaster.{broadcaster}")
        if not utils.checkSetup(): 
            res = BroadcasterResult()
            res.Url = ""
            res.UseInputStreamAdaptive = False
        else:
            res = c.play(channel)
    else:
        utils.MessageBox(f"Sorry, broadcaster '{broadcaster}' not found")

    if res:
        if res.PlayableMediaItems:
            utils.createPlayableMediaListItemsMenu(plugin.handle, "", True, res.PlayableMediaItems)
        else:
            makeListItemToPlay(res)
    else:
        xbmcplugin.setResolvedUrl(plugin.handle, True, xbmcgui.ListItem())


####
# Build a fake-listitem in order to set all details to make kodi simply playing
###
def makeListItemToPlay(bdcRes: BroadcasterResult, userAgent: str = None):
    if not bdcRes: return

    # res = string
    # or
    # input = {'url':      required,
    #          'licenceKey':   optional, required for drm streams,
    #          'licenceType':  optional, default 'com.widevine.alpha'}
    #          'streamHeader': optional, streams header,

    kodiVersion = utils.getInstalledVersion()
    
    xlistitem = None

    if type(bdcRes.Url) == list and len(bdcRes.Url) == 1:
        bdcRes.Url = bdcRes.Url[0]

    if type(bdcRes.Url) == list:
        winTitle = "Video"
        lstItem = list()
        idx = 0
        for url in bdcRes.Url:
            idx=idx+1
            title = f"{bdcRes.Title} (Video {idx})".strip()
            lstItem.append(utils.getListItem(title, url, mediatype="video", isFolder=False))

        idx = xbmcgui.Dialog().select(f"{config.getString(30185)} {winTitle}", lstItem)
        if idx < 0:
            bdcRes.Url = "x"
        else:
            bdcRes.Url = lstItem[idx].getPath()

    if bdcRes.Url == "x": return
    if not bdcRes.Url:
        bdcRes = BroadcasterResult
        bdcRes.Url = utils.VIDEO_NOT_FOUND
        bdcRes.UseInputStreamAdaptive = False
        utils.MessageBox(30203)
        
    if bdcRes.Url:

        if bdcRes.UserAgent == True:
            logger.debug(f"UserAgent required, default will be set")
            bdcRes.UserAgent = const.USER_AGENT
        elif bdcRes.UserAgent == False or not bdcRes.UserAgent:
            logger.debug(f"UserAgent not specified")
            bdcRes.UserAgent = None
        elif bdcRes.UserAgent:
            logger.debug(f"UserAgent provided, {bdcRes.UserAgent} will be set")

        if bdcRes.UserAgent:
            bdcRes.StreamHeaders["User-Agent"] = bdcRes.UserAgent
            
        if bdcRes.VerifyPeer == False:
            bdcRes.StreamHeaders["verifypeer"] = "false"

        if not bdcRes.UseInputStreamAdaptive and bdcRes.StreamHeaders:
            headersString = '&'.join([f'{k}={v}' for k, v in bdcRes.StreamHeaders.items()])
            bdcRes.Url = f"{bdcRes.Url}|{headersString}"

        # make item
        xlistitem = xbmcgui.ListItem(path=bdcRes.Url)
        if bdcRes.Title:
            xlistitem.setInfo("video", {"title": bdcRes.Title})
        if bdcRes.Plot:
            xlistitem.setInfo("video", {"plot": bdcRes.Plot})

        
        if bdcRes.Subtitles:
            xlistitem.setSubtitles(bdcRes.Subtitles)
        logger.debug("Playing: ", bdcRes.Url)

    if not xlistitem:
        logger.error("NO URL found for channel")
        xbmcgui.Dialog().notification(config.getString(30000), config.getString(30123), xbmcgui.NOTIFICATION_WARNING)
        return

    if bdcRes.UseInputStreamAdaptive:
        installInputStreamAdaptive()  # Check if inputstream is installed otherwise install it

        # add parameters for inputstream
        xlistitem.setProperty("inputstream","inputstream.adaptive")

#kodi20
        if kodiVersion == 20:
            bdcRes.ManifestType = 'mpd' if '.mpd' in bdcRes.Url else 'hls'
            if bdcRes.ManifestType:
                xlistitem.setProperty("inputstream.adaptive.manifest_type",bdcRes.ManifestType)
            xlistitem.setMimeType("application/dash+xml" if bdcRes.ManifestType == "mpd" else "application/x-mpegURL")

            if bdcRes.ManifestUpdateParameter:
                xlistitem.setProperty("inputstream.adaptive.manifest_update_parameter", bdcRes.ManifestUpdateParameter)
#/kodi20
        if bdcRes.DRMLegacy:
            installWidevine()
            xlistitem.setProperty("inputstream.adaptive.drm_legacy",  bdcRes.LicenseKey)

        if bdcRes.LicenseKey: # add parameters for drm
            installWidevine()
            xlistitem.setProperty("inputstream.adaptive.license_key",  bdcRes.LicenseKey)
            xlistitem.setProperty("inputstream.adaptive.license_type", bdcRes.LicenseType)
            if bdcRes.LongLicenseUrl:
                part1 = bdcRes.LongLicenseUrl[:1024]
                part2 = bdcRes.LongLicenseUrl[1024:]

                xlistitem.setProperty('inputstream.adaptive.license_url', part1)
                xlistitem.setProperty('inputstream.adaptive.license_url_append', part2)

        if bdcRes.ManifestHeaders:
            xlistitem.setProperty("inputstream.adaptive.manifest_headers", urlencode(bdcRes.ManifestHeaders))

        if bdcRes.StreamHeaders:
            xlistitem.setProperty("inputstream.adaptive.stream_headers",  urlencode(bdcRes.StreamHeaders))
            xlistitem.setProperty("inputstream.adaptive.manifest_headers", urlencode(bdcRes.StreamHeaders))

        if bdcRes.StreamSelectionType:
            xlistitem.setProperty("inputstream.adaptive.stream_selection_type", bdcRes.StreamSelectionType)

        if bdcRes.Delay > 16:
            logger.info(f"Setting {bdcRes.Delay} sec. of delay....")
            xlistitem.setProperty('inputstream.adaptive.live_delay', str(bdcRes.Delay))

    forceStopForSwitch = config.getSetting("forceStopForSwitch")

    # Stop Video Before Playing (For underperforming devices)
    if forceStopForSwitch:
        bdcRes.ForceStopBeforePlay = True

    if bdcRes.ForceStopBeforePlay:
        logger.debug("force stop as per user or broadcaster settings")
        xbmc.Player().stop()
 
    playlist = None
    
    if bdcRes.PlayerMode != 0:
        xbmc.executebuiltin('Dialog.Close(all,true)')
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add(xlistitem.getPath(), xlistitem)
        
    # play item
    playVideo(playlist, xlistitem)

    bdcRes = None


def playVideo(playlist, xlistitem):
    kodiPlayer = xbmc.Player()

    if not playlist:
        xbmcplugin.setResolvedUrl(plugin.handle, True, xlistitem)
    else:
        kodiPlayer.play(playlist, xlistitem)
