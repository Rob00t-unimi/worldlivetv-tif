# -*- coding: utf-8 -*-

SORT_METHOD_NONE = 0
SORT_METHOD_LABEL_IGNORE_THE = 1


def setPluginCategory(handle, category):
    pass


def setContent(handle, content):
    pass


def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
    return True


def addSortMethod(handle, sortMethod):
    pass


def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
    pass


def setResolvedUrl(handle, succeeded, listitem):
    pass
