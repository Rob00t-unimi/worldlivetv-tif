# -*- coding: utf-8 -*-
import os
import re

_DATA_DIR = os.environ.get("WLTV_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
_WLTV_DIR = os.environ.get("WLTV_CODE_DIR", os.path.join(os.path.dirname(__file__), "..", "wltv"))

_DEFAULT_SETTINGS = {
    "raimpd": "true",
    "raidelay": "0",
    "rai3config": "0.0.300",
    "discoverympd": "true",
    "discoverydelay": "0",
    "enable_epg": "true",
    "resolutions": "0",
    "forceStopForSwitch": "false",
    "internalListNavigation": "true",
    "localFileExpiringDays": "1",
    "hide_default_list": "false",
    "MediasetUsername": "",
    "MediasetPassword": "",
}


def _detect_addon_version() -> str:
    data_dir = os.environ.get("WLTV_DATA_DIR", _DATA_DIR)
    wltv_dir = os.environ.get("WLTV_CODE_DIR", _WLTV_DIR)
    candidates = [
        os.path.join(data_dir, "addon_overlay", "addon.xml"),
        os.path.join(wltv_dir, "addon.xml"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    m = re.search(r'<addon[^>]+id="plugin\.video\.wltvhelper"[^>]+version="([^"]+)"', f.read())
                    if m:
                        return m.group(1)
            except Exception:
                pass
    return "1.2.14"


class Addon:
    def __init__(self, id="plugin.video.wltvhelper"):
        self._id = id
        self._settings = dict(_DEFAULT_SETTINGS)

    def getAddonInfo(self, info_id: str) -> str:
        key = info_id.lower()
        if key == "id":
            return self._id
        if key == "name":
            return "World Live TV"
        if key == "version":
            return _detect_addon_version()
        if key == "path":
            overlay = os.path.join(os.environ.get("WLTV_DATA_DIR", _DATA_DIR), "addon_overlay")
            if os.path.isdir(overlay):
                return overlay
            return os.environ.get("WLTV_CODE_DIR", _WLTV_DIR)
        if key == "profile":
            profile_dir = os.path.join(os.environ.get("WLTV_DATA_DIR", _DATA_DIR), "profile", self._id)
            os.makedirs(profile_dir, exist_ok=True)
            return profile_dir
        return ""

    def getSetting(self, setting_id: str) -> str:
        return self._settings.get(setting_id, "")

    def setSetting(self, setting_id: str, value: str):
        self._settings[setting_id] = str(value)

    def openSettings(self):
        pass

    def getLocalizedString(self, string_id: int) -> str:
        return f"str_{string_id}"
