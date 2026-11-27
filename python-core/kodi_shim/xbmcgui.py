# -*- coding: utf-8 -*-

NOTIFICATION_INFO = "info"
NOTIFICATION_WARNING = "warning"
NOTIFICATION_ERROR = "error"
INPUT_ALPHANUM = 0

_WINDOW_PROPS = {}


class Window:
    def __init__(self, window_id: int = 10000):
        self._id = window_id
        if window_id not in _WINDOW_PROPS:
            _WINDOW_PROPS[window_id] = {}

    def getProperty(self, key: str) -> str:
        return _WINDOW_PROPS[self._id].get(key, "")

    def setProperty(self, key: str, value: str):
        _WINDOW_PROPS[self._id][key] = str(value)

    def clearProperty(self, key: str):
        _WINDOW_PROPS[self._id].pop(key, None)


class Dialog:
    def ok(self, heading: str, message: str) -> bool:
        return True

    def yesno(self, heading: str, message: str) -> bool:
        return True

    def notification(self, heading: str, message: str, icon=None, time: int = 5000):
        pass

    def select(self, heading: str, list_items) -> int:
        return 0

    def input(self, heading: str, defaultt: str = "", type: int = 0) -> str:
        return defaultt

    def browse(self, *args, **kwargs) -> str:
        return ""

    def browseSingle(self, *args, **kwargs) -> str:
        return ""


class DialogProgress:
    def create(self, heading: str, message: str = ""):
        pass

    def update(self, percent: int, message: str = ""):
        pass

    def close(self):
        pass

    def iscanceled(self) -> bool:
        return False


class ListItem:
    def __init__(self, label: str = "", label2: str = "", path: str = ""):
        self._label = label
        self._path = path
        self._props = {}

    def getLabel(self) -> str:
        return self._label

    def getPath(self) -> str:
        return self._path

    def setArt(self, art: dict):
        pass

    def setInfo(self, type: str, infoLabels: dict):
        pass

    def setProperty(self, key: str, value: str):
        self._props[key] = value

    def setMimeType(self, mimetype: str):
        pass

    def setSubtitles(self, subtitles):
        pass


class WindowXMLDialog:
    def __init__(self, *args, **kwargs):
        pass
