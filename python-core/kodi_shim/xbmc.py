# -*- coding: utf-8 -*-
import os
import time

LOGDEBUG = 0
LOGINFO = 1
LOGWARNING = 2
LOGERROR = 3
LOGFATAL = 4
LOGNONE = 5

PLAYLIST_VIDEO = 1
PLAYLIST_MUSIC = 0

_BASE_DIR = os.environ.get("WLTV_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))


def translatePath(path: str) -> str:
    if path.startswith("special://home/addons/"):
        return os.path.join(_BASE_DIR, "addons", path[len("special://home/addons/"):])
    if path.startswith("special://userdata/addon_data/"):
        return os.path.join(_BASE_DIR, "addon_data", path[len("special://userdata/addon_data/"):])
    if path.startswith("special://profile/addon_data/"):
        return os.path.join(_BASE_DIR, "addon_data", path[len("special://profile/addon_data/"):])
    if path.startswith("special://logpath"):
        return os.path.join(_BASE_DIR, "logs")
    if path.startswith("special://database"):
        return os.path.join(_BASE_DIR, "database")
    return path


def log(msg: str, level: int = LOGINFO):
    # Uncomment for verbose debug:
    # print(f"[XBMC:{level}] {msg}")
    pass


def sleep(ms: int):
    time.sleep(ms / 1000.0)


def executebuiltin(cmd: str, wait: bool = False):
    pass


def executeJSONRPC(json_str: str) -> str:
    return "{}"


def getCondVisibility(condition: str) -> bool:
    if "system.platform.android" in condition.lower():
        return os.environ.get("WLTV_ANDROID", "0") == "1"
    return False


class Player:
    def stop(self):
        pass

    def play(self, *args, **kwargs):
        pass


class PlayList:
    def __init__(self, playlist_id):
        self.items = []

    def clear(self):
        self.items.clear()

    def add(self, url, listitem=None):
        self.items.append((url, listitem))
