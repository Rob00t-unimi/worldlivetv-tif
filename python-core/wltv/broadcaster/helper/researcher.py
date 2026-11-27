# -*- coding: utf-8 -*-

from lib import scrapers, logger


def GetLink(data):
    url = scrapers.findSingleMatch(data, r'<video.*?src="([^"]+)')

    if not url:
        url = scrapers.findSingleMatch(data, r'<source\s+type="application/x-mpegURL"\s+src="([^"]+)"')
    if not url:
        url = scrapers.findSingleMatch(data, r'<source\s?src="([^"]+)')
    if not url:
        url = scrapers.findSingleMatch(data, r'source\s?src="([^"]+)')
    if not url:
        url = scrapers.findSingleMatch(data, r'"source":\s?"([^"]+)')
    if not url:
        url = scrapers.findSingleMatch(data, r'source\s?:\s?"([^"]+)')

    return url
