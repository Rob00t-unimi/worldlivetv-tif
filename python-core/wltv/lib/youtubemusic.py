# Module: UnitedMusic
# Author: CrAcK75
# Created on: 09/05/2021
#

import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import base64
import zlib
import requests
import routing
import json
import urllib
from lib import logger, config, utils

_name = "YouTubeMusic"
fileName = f"List{_name}.bin"

plugin = routing.Plugin()


@plugin.route("/youtubemusic")
def Start():
    ShowGroups()

def ShowGroups():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, _name)

    lstItem = GetLists()
    if not lstItem:
        return

    #"Groups":["Karaoke","Music","Relax"],"Channels":
    lstGroups = lstItem.get("Groups", [])
    if not lstGroups:
        return

    for group in lstGroups:
        li = xbmcgui.ListItem(group)

        url = plugin.url_for(ShowChannels, group)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)

@plugin.route("/youtubemusic/searchvideo/<group>")
def SearchVideo(group):
    handle = plugin.handle
    
    strSearch = config.getString(30156)
    xbmcplugin.setPluginCategory(handle, f"{_name} - {strSearch}")
    xbmcplugin.setContent(handle, "videos")

    keyboard = xbmc.Keyboard("", f"{strSearch}?")
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        query = keyboard.getText().strip()

        if query:
            lstItem = GetVideosSearch(group, query, GetLists())
    
            for item in lstItem:
                title = item["Title"]
                logo  = item["Logo"]
                url   = item["KodiUrl"]
        
                song   = ""
                artist = ""
                genre  = ""
                year   = ""
                album  = ""

                li = xbmcgui.ListItem(title)
                li.setArt(
                    {
                        "thumb":  logo,
                        "poster": logo,
                        "fanart": logo,
                    }
                )
                li.setInfo(
                    "video",
                    {
                        "year":   year,
                        "album":  album,
                        "artist": [artist],
                        "title":  f"{title} - {artist}",
                        "mediatype": "song",
                    },
                )

                li.setProperty("IsPlayable", "true")
                xbmcplugin.addDirectoryItem(handle, url, li, False)

    xbmcplugin.endOfDirectory(handle)

@plugin.route("/youtubemusic/showchannels/<group>")
def ShowChannels(group):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, _name)

    lstItem = GetChannels(group, GetLists())
    if not lstItem:
        return

    url = plugin.url_for(SearchVideo, group)
    utils.addMenuItem(handle, 30156, url,icon="search", fanart="search",isFolder=True)

    for item in lstItem: 
        name = item["Name"]
        group = item["Group"]
        code  = item["ChannelId"]
        genre = item["Genre"]
        descr = item["Description"]

        itemName = f"{name} - {group}"

        url = plugin.url_for(ShowVideos, itemName, code)
        utils.addMenuItemPlayable(handle=handle, title=itemName, url=url, plot=descr, icon=item["Logo"], thumb="", poster="", fanart="", genre=genre, year="", mediatype="music", isFolder=True)

    xbmcplugin.endOfDirectory(handle)

@plugin.route("/youtubemusic/showvideos/<name>/<code>")
def ShowVideos(name, code):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, name)
    xbmcplugin.setContent(handle, "videos")

    lstItem = GetChannel(code, GetLists())

    for item in lstItem.get("Videos", []):
        title = item["Title"]
        logo  = item["Logo"]
        url   = item["KodiUrl"]
        
        song   = ""
        artist = lstItem["Name"]
        genre  = lstItem["Genre"]
        year   = ""
        album  = ""

        li = xbmcgui.ListItem(title)
        li.setArt(
            {
                "thumb":  logo,
                "poster": logo,
                "fanart": logo,
            }
        )
        li.setInfo(
            "video",
            {
                "year":   year,
                "album":  album,
                "artist": [artist],
                "title":  f"{title} - {artist}",
                "mediatype": "song",
            },
        )

        li.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle, url, li, False)

    xbmcplugin.endOfDirectory(handle)

def GetVideosSearch(group, text, lstItem):
    return [v for c in lstItem.get("Channels", []) for v in c["Videos"] if text.lower() in v["Title"].lower()]

def GetChannels(group, lstItem):
    return list(filter(lambda item: item["Group"] == group, lstItem.get("Channels", [])))

def GetChannel(code, lstItem):
    return [x for x in lstItem.get("Channels", []) if x["ChannelId"] == code][0]

def GetLists():
    return utils.GetJsonList(fileName)

plugin.run()
