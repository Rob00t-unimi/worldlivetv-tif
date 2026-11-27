# WorldLiveTV TIF (Android TV / Live Channels)

A lightweight IPTV client for **Android TV** (built for **Firestick with LineageOS** and **TV Input Framework / Live Channels** compatible devices) that natively runs the **WorldLiveTV** Python resolver engine without requiring Kodi.

---

## Credits & Upstream Source

This project builds upon and integrates with the public code and endpoints of **WorldLiveTV**:
- **Original Repository**: [WorldLiveTV / WorldLiveTV.github.io](https://github.com/WorldLiveTV/WorldLiveTV.github.io)
- **Original Kodi Add-on**: `plugin.video.wltvhelper` (`WLTV Group`, GPL-3.0-or-later)
- **Website / Kodi Repo**: https://worldlivetv.github.io/

All credit for the broadcaster scrapers, channel lists, and EPG goes to the **WorldLiveTV** team. This repository solely provides the Android TV / TIF compatibility layer to run those modules outside of Kodi.

---

## How It Works

Inside Kodi, WorldLiveTV M3U8 playlists do not contain direct stream URLs; instead, they contain internal plugin URLs such as:
```text
plugin://plugin.video.wltvhelper/?play/<broadcaster>/<channel>
```
which are resolved on-demand at tune time by the Python modules in `broadcaster/*.py` (handling temporary tokens, custom HTTP headers, and Widevine DRM licenses).

This repository replicates the exact same mechanism on Android TV through two components:

### 1. `python-core/` — Python Engine & Kodi Micro-Shim
- **`kodi_shim/`**: lightweight compatibility layer implementing the Kodi APIs used by the broadcasters (`xbmc`, `xbmcaddon`, `xbmcgui`, `xbmcvfs`, `xbmcplugin`, `routing`).
- **`wltv/`**: `broadcaster/` and `lib/` modules extracted from `plugin.video.wltvhelper`.
- **`wltv_bridge.py`**: unified bridge (usable both from desktop CLI tests and from Android via Chaquopy) exposing:
  - `check_addon_release()` & `check_hotfix()`: automatically checks `addons.xml` and `hotfix.json` on WorldLiveTV's GitHub repo and downloads newer releases or hotfixes into local overlays (`addon_overlay/`, `hotfix_overlay/`), without rebuilding the APK.
  - `get_remote_lists()` & `fetch_m3u_channels()`: fetches and parses official playlists from `tvchannels.worldtvlive.eu`.
  - `fetch_epg_programs()`: downloads and decompresses the XMLTV EPG (`wltv.xz`) to populate the TV guide.
  - `resolve_channel()`: runs `broadcaster.<name>.play(channel)` and returns the resolved stream URL, manifest type (`hls`/`mpd`), HTTP headers, and Widevine `LicenseKey` configuration.
- **`test_broadcasters.py`**: desktop test script to verify channel resolution (Rai, Mediaset, La7, Discovery) and the hotfix updater.

### 2. `android-tv-app/` — Android TV App (Kotlin + TIF + Media3 + Chaquopy)
Inspired by Google's official [`googlesamples/androidtv-sample-inputs`](https://github.com/googlesamples/androidtv-sample-inputs) blueprint, modernized with **Kotlin**, **AndroidX**, **Media3 ExoPlayer 1.5.0**, and **Chaquopy 15.0.1**:
- **`WltvTvInputService`**: implements `android.media.tv.TvInputService` for native **Android TV Live Channels (TIF)** integration. On channel tune, it resolves the stream via Python and renders it onto the system TIF `Surface`.
- **`ExoPlayerBuilder`**: configures Media3 `ExoPlayer` for HLS and DASH, applies `StreamHeaders`/`ManifestHeaders`, and parses Kodi InputStream Adaptive `LicenseKey` strings for `DefaultDrmSessionManager` (Widevine).
- **`SetupActivity` & `ChannelSyncWorker`**: lets the user pick a WorldLiveTV playlist and syncs channels (`TvContract.Channels`) and EPG programs (`TvContract.Programs`) into the system `TvProvider`.
- **`MainActivity` & `PlayerActivity`**: standalone fallback UI to browse playlists/channels and play them directly with Media3 on devices without Live Channels.

---

## Requirements & Build

### Desktop Python Tests
```bash
cd python-core
pip install requests
python test_broadcasters.py
```

### Android TV APK Build
1. Open `android-tv-app/` in Android Studio (or use Gradle CLI with JDK 17 and Android SDK 35).
2. Build the debug APK:
   ```bash
   cd android-tv-app
   ./gradlew assembleDebug
   ```
3. Install on Firestick / Android TV via ADB:
   ```bash
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

---

## Disclaimer
This project is intended for educational purposes and personal interoperability to watch free-to-air (FTA) television channels via the Android TV Input Framework. No video streams are hosted in this repository.
