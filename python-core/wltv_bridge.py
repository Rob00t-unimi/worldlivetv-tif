# -*- coding: utf-8 -*-
"""
Unified Python bridge for WorldLiveTV.
Works both standalone on desktop (for testing) and inside Android (via Chaquopy).
"""
import importlib
import io
import json
import lzma
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
import requests

_INITIALIZED = False
_DATA_DIR = ""
_WLTV_DIR = ""

ADDON_REPO_BASE = "https://worldlivetv.github.io/repo"


def init(data_dir: str = "", wltv_dir: str = ""):
    global _INITIALIZED, _DATA_DIR, _WLTV_DIR
    if _INITIALIZED:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = data_dir or os.path.join(base_dir, "data")
    _WLTV_DIR = wltv_dir or os.path.join(base_dir, "wltv")

    os.makedirs(_DATA_DIR, exist_ok=True)
    os.environ["WLTV_DATA_DIR"] = _DATA_DIR
    os.environ["WLTV_CODE_DIR"] = _WLTV_DIR

    shim_dir = os.path.join(base_dir, "kodi_shim")
    for p in (shim_dir, _WLTV_DIR):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Priority order: hotfix_overlay -> addon_overlay -> bundled wltv
    for sub in ("addon_overlay", "hotfix_overlay"):
        d = os.path.join(_DATA_DIR, sub)
        if os.path.isdir(d) and d not in sys.path:
            sys.path.insert(0, d)

    _INITIALIZED = True


def _ver_tuple(v: str):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def check_addon_release() -> dict:
    """Checks addons.xml on WorldLiveTV GitHub repo and downloads newer full addon releases."""
    init()
    from lib import config
    addon_overlay = os.path.join(_DATA_DIR, "addon_overlay")
    try:
        resp = requests.get(f"{ADDON_REPO_BASE}/addons.xml", timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        target_ver = None
        for addon_el in root.findall("addon"):
            if addon_el.attrib.get("id") == "plugin.video.wltvhelper":
                target_ver = addon_el.attrib.get("version")
                break
        if not target_ver:
            return {"addon_updated": False, "reason": "not found in addons.xml"}

        current_ver = config.ADDON.getAddonInfo("version")
        if _ver_tuple(target_ver) <= _ver_tuple(current_ver):
            return {"addon_updated": False, "version": current_ver}

        zip_url = f"{ADDON_REPO_BASE}/plugin.video.wltvhelper/plugin.video.wltvhelper-{target_ver}.zip"
        zresp = requests.get(zip_url, timeout=30)
        zresp.raise_for_status()
        os.makedirs(addon_overlay, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(zresp.content)) as zf:
            for member in zf.namelist():
                parts = member.split("/", 1)
                if len(parts) == 2 and parts[1] and not parts[1].endswith("/"):
                    out_path = os.path.join(addon_overlay, parts[1])
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with zf.open(member) as src, open(out_path, "wb") as dst:
                        dst.write(src.read())

        if addon_overlay not in sys.path:
            sys.path.insert(0, addon_overlay)
        config.ADDON_VERSION = target_ver
        importlib.invalidate_caches()
        return {"addon_updated": True, "version": target_ver}
    except Exception as e:
        return {"addon_updated": False, "error": str(e)}


def check_hotfix() -> str:
    """Checks both full addon release (addons.xml) and hotfix.json on WorldLiveTV GitHub."""
    init()
    release_info = check_addon_release()

    from lib import config, utils
    url_info = f"{utils.ADDON_REPO_HOTFIX}/{utils.HOTFIX_FILE_INFO}"
    overlay_dir = os.path.join(_DATA_DIR, "hotfix_overlay")
    local_info_path = os.path.join(_DATA_DIR, "hotfix.json")
    current_ver = config.ADDON.getAddonInfo("version")

    try:
        server_list = requests.get(url_info, timeout=10).json()
        target = next((h for h in server_list if h.get("destination") == current_ver), None)
        if not target:
            return json.dumps({**release_info, "updated": False, "version": current_ver, "reason": "no matching hotfix"})

        local_hotfix = 0
        if os.path.isfile(local_info_path):
            with open(local_info_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if saved.get("destination") == current_ver:
                    local_hotfix = int(saved.get("hotfix", 0))

        server_hotfix = int(target.get("hotfix", 0))
        if server_hotfix > local_hotfix:
            zip_url = f"{utils.ADDON_REPO_HOTFIX}/{target['filename']}"
            resp = requests.get(zip_url, timeout=20)
            resp.raise_for_status()
            os.makedirs(overlay_dir, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                for member in zf.namelist():
                    parts = member.split("/", 1)
                    if len(parts) == 2 and parts[1] and not parts[1].endswith("/"):
                        out_path = os.path.join(overlay_dir, parts[1])
                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                        with zf.open(member) as src, open(out_path, "wb") as dst:
                            dst.write(src.read())
            with open(local_info_path, "w", encoding="utf-8") as f:
                json.dump(target, f)
            if overlay_dir not in sys.path:
                sys.path.insert(0, overlay_dir)
            importlib.invalidate_caches()
            return json.dumps({**release_info, "updated": True, "version": current_ver, "hotfix": server_hotfix, "description": target.get("description", "")})
        return json.dumps({**release_info, "updated": False, "version": current_ver, "hotfix": local_hotfix})
    except Exception as e:
        return json.dumps({**release_info, "updated": False, "version": current_ver, "error": str(e)})


def get_remote_lists() -> str:
    """Returns JSON list of available official WorldLiveTV lists."""
    init()
    from lib import utils
    custom_lists = utils.getRemoteLists()
    out = []
    for cl in custom_lists:
        m3u = cl.Lists[0] if cl.Lists else None
        out.append({
            "id": cl.Id,
            "name": cl.Name,
            "type": str(cl.TypeOfList),
            "url": utils.computeListUrl(cl) if str(cl.TypeOfList) != "ListType.Emergency" else (m3u.List if m3u else ""),
            "epg": utils.EPG_URL,
        })
    return json.dumps(out)


def fetch_m3u_channels(m3u_url: str) -> str:
    """Downloads an M3U8 list from WorldLiveTV and parses channels into JSON."""
    init()
    from lib import const
    resp = requests.get(m3u_url, headers={"User-Agent": const.USER_AGENT}, timeout=15)
    resp.raise_for_status()
    channels = []
    current_meta = {}
    for raw_line in resp.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            current_meta = _parse_extinf(line)
        elif not line.startswith("#"):
            plugin_info = _parse_plugin_url(line)
            channels.append({
                "name": current_meta.get("name", "Unknown"),
                "tvgId": current_meta.get("tvg-id", ""),
                "tvgLogo": current_meta.get("tvg-logo", ""),
                "tvgChNo": current_meta.get("tvg-chno", ""),
                "group": current_meta.get("group-title", ""),
                "rawUrl": line,
                **plugin_info,
            })
            current_meta = {}
    return json.dumps(channels)


def _parse_xmltv_time(ts: str) -> int:
    # Format: 20261127150000 +0100
    m = re.match(r"(\d{14})\s*([+-]\d{4})?", ts.strip())
    if not m:
        return 0
    dt = datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
    if m.group(2):
        sign = 1 if m.group(2)[0] == "+" else -1
        hh = int(m.group(2)[1:3])
        mm = int(m.group(2)[3:5])
        from datetime import timedelta
        tz = timezone(sign * timedelta(hours=hh, minutes=mm))
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def fetch_epg_programs(channel_ids_json: str, max_per_channel: int = 20) -> str:
    """Downloads wltv.xz EPG and returns programs matching the given tvgId set as JSON."""
    init()
    from lib import utils
    wanted = set(json.loads(channel_ids_json))
    if not wanted:
        return json.dumps({})

    epg_cache = os.path.join(_DATA_DIR, "wltv_epg.xml")
    need_dl = True
    if os.path.isfile(epg_cache):
        age_sec = datetime.now().timestamp() - os.path.getmtime(epg_cache)
        if age_sec < 6 * 3600:
            need_dl = False

    if need_dl:
        resp = requests.get(utils.EPG_URL, timeout=30)
        resp.raise_for_status()
        xml_bytes = lzma.decompress(resp.content)
        with open(epg_cache, "wb") as f:
            f.write(xml_bytes)

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    programs = {}
    for _, elem in ET.iterparse(epg_cache, events=("end",)):
        if elem.tag == "programme":
            ch_id = elem.attrib.get("channel", "")
            if ch_id in wanted:
                start_ms = _parse_xmltv_time(elem.attrib.get("start", ""))
                stop_ms = _parse_xmltv_time(elem.attrib.get("stop", ""))
                if stop_ms > now_ms:
                    lst = programs.setdefault(ch_id, [])
                    if len(lst) < max_per_channel:
                        title_el = elem.find("title")
                        desc_el = elem.find("desc")
                        lst.append({
                            "title": title_el.text if title_el is not None and title_el.text else "",
                            "desc": desc_el.text if desc_el is not None and desc_el.text else "",
                            "startMs": start_ms,
                            "stopMs": stop_ms,
                        })
            elem.clear()
    return json.dumps(programs)


def _parse_extinf(line: str) -> dict:
    meta = {}
    for k, v in re.findall(r'([a-zA-Z0-9_-]+)="([^"]*)"', line):
        meta[k.lower()] = v
    comma_idx = line.rfind(",")
    if comma_idx != -1:
        meta["name"] = line[comma_idx + 1:].strip()
    return meta


def _parse_plugin_url(url: str) -> dict:
    if url.startswith("plugin://plugin.video.wltvhelper/"):
        path = url.split("plugin://plugin.video.wltvhelper/", 1)[1].lstrip("?")
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "play":
            if len(parts) >= 6:
                return {
                    "broadcaster": parts[1],
                    "channel": parts[2],
                    "listName": parts[3],
                    "groupId": parts[4],
                    "channelId": parts[5],
                }
            return {
                "broadcaster": parts[1],
                "channel": "/".join(parts[2:]),
            }
    return {"broadcaster": "direct", "channel": url}


def resolve_channel(broadcaster: str, channel: str, list_name: str = "", group_id: str = "", channel_id: str = "") -> str:
    """
    Resolves a channel using WorldLiveTV's broadcaster modules (or tvchannels fallback).
    Returns JSON with url, licenseKey, licenseType, streamHeaders, manifestHeaders, etc.
    """
    init()
    from lib import const, utils

    if broadcaster in ("direct", ""):
        return json.dumps({"url": channel, "useInputStreamAdaptive": False})

    if broadcaster == "none" and list_name:
        api_key = utils.getApikeyParameter()
        url = f"{utils.API_DOMAIN}/{list_name}/live?{api_key}channel={channel_id}&group={group_id}"
        resp = requests.get(url, allow_redirects=False, timeout=10)
        if 299 < resp.status_code < 304:
            loc = resp.headers.get("Location", "")
            if loc.startswith("plugin://"):
                parsed = _parse_plugin_url(loc)
                return resolve_channel(parsed.get("broadcaster", ""), parsed.get("channel", ""))
            url = loc
        return json.dumps({"url": url, "useInputStreamAdaptive": False})

    try:
        mod = importlib.import_module(f"broadcaster.{broadcaster}")
        res = mod.play(channel)
        if not res:
            return json.dumps({"error": "Empty BroadcasterResult"})

        stream_headers = dict(res.StreamHeaders) if isinstance(res.StreamHeaders, dict) else {}
        manifest_headers = dict(res.ManifestHeaders) if isinstance(res.ManifestHeaders, dict) else {}

        if res.UserAgent is True:
            stream_headers.setdefault("User-Agent", const.USER_AGENT)
        elif isinstance(res.UserAgent, str) and res.UserAgent:
            stream_headers.setdefault("User-Agent", res.UserAgent)

        url = res.Url[0] if isinstance(res.Url, list) and res.Url else (res.Url or "")
        return json.dumps({
            "title": res.Title or "",
            "url": url,
            "useInputStreamAdaptive": bool(res.UseInputStreamAdaptive),
            "licenseKey": res.LicenseKey or "",
            "licenseType": res.LicenseType or "com.widevine.alpha",
            "streamHeaders": stream_headers,
            "manifestHeaders": manifest_headers,
            "manifestType": res.ManifestType or ("mpd" if ".mpd" in str(url) else "hls"),
            "delay": res.Delay or 0,
        })
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
