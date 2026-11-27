# -*- coding: utf-8 -*-

import xbmcgui
import base64
import zlib
import time


def get_or_set_string(key, value="", expire_minutes=60):
    """
    Sets or gets a string from Kodi cache with expiration support.
    :param key: Unique key.
    :param value: Value to store.
    :param expire_minutes: Expiration time in minutes (0 = never expires).
    """
    if value:
        set_kodi_string(key, value, expire_minutes)
    else:
        return get_kodi_string(key)


def set_kodi_string(key, value, expire_minutes=60):
    _key = base64.b64encode(key.encode()).decode()
    _value = base64.b64encode(zlib.compress(value.encode())).decode()
    
    expire_time = int(time.time()) + (expire_minutes * 60) if expire_minutes > 0 else 0
    
    data = f"{expire_time}|{_value}"
    
    xbmcgui.Window(10000).setProperty(_key, data)


def get_kodi_string(key, default=""):
    _key = base64.b64encode(key.encode()).decode()
    data = xbmcgui.Window(10000).getProperty(_key)
    
    if data:
        try:
            expire_time, _value = data.split("|", 1)
            expire_time = int(expire_time)
            
            if expire_time > 0 and time.time() > expire_time:
                xbmcgui.Window(10000).clearProperty(_key)
                return default
            
            return zlib.decompress(base64.b64decode(_value)).decode()
        
        except Exception as e:
            print(f"Cache decode error: {e}")
    
    return default

