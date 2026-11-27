package com.wltv.tif.player

import android.content.Context
import android.net.Uri
import androidx.annotation.OptIn
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.common.util.UnstableApi
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.dash.DashMediaSource
import androidx.media3.exoplayer.drm.DefaultDrmSessionManager
import androidx.media3.exoplayer.drm.FrameworkMediaDrm
import androidx.media3.exoplayer.drm.HttpMediaDrmCallback
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import androidx.media3.exoplayer.source.MediaSource
import com.wltv.tif.bridge.ResolvedStream
import java.net.URLDecoder

object ExoPlayerBuilder {

    @OptIn(UnstableApi::class)
    fun buildAndPrepare(context: Context, stream: ResolvedStream): ExoPlayer {
        val headers = HashMap<String, String>().apply {
            putAll(stream.manifestHeaders)
            putAll(stream.streamHeaders)
        }
        val userAgent = headers["User-Agent"] ?: "Mozilla/5.0"

        val httpFactory = DefaultHttpDataSource.Factory()
            .setUserAgent(userAgent)
            .setAllowCrossProtocolRedirects(true)
            .setDefaultRequestProperties(headers)

        val mediaSourceFactory: MediaSource.Factory = when {
            stream.manifestType == "mpd" || stream.url.contains(".mpd") ->
                DashMediaSource.Factory(httpFactory)
            stream.manifestType == "hls" || stream.url.contains(".m3u8") ->
                HlsMediaSource.Factory(httpFactory)
            else ->
                DefaultMediaSourceFactory(httpFactory)
        }

        if (stream.licenseKey.isNotBlank()) {
            val (licenseUrl, licenseHeaders) = parseKodiLicenseKey(stream.licenseKey)
            if (licenseUrl.isNotBlank()) {
                val drmHttpFactory = DefaultHttpDataSource.Factory()
                    .setUserAgent(licenseHeaders["User-Agent"] ?: userAgent)
                    .setAllowCrossProtocolRedirects(true)
                    .setDefaultRequestProperties(licenseHeaders)

                val drmCallback = HttpMediaDrmCallback(licenseUrl, drmHttpFactory)
                val drmSessionManager = DefaultDrmSessionManager.Builder()
                    .setUuidAndExoMediaDrmProvider(C.WIDEVINE_UUID, FrameworkMediaDrm.DEFAULT_PROVIDER)
                    .build(drmCallback)

                mediaSourceFactory.setDrmSessionManagerProvider { drmSessionManager }
            }
        }

        val mimeType = when {
            stream.manifestType == "mpd" || stream.url.contains(".mpd") -> MimeTypes.APPLICATION_MPD
            stream.manifestType == "hls" || stream.url.contains(".m3u8") -> MimeTypes.APPLICATION_M3U8
            else -> null
        }

        val mediaItem = MediaItem.Builder()
            .setUri(Uri.parse(stream.url))
            .apply { if (mimeType != null) setMimeType(mimeType) }
            .build()

        return ExoPlayer.Builder(context).build().apply {
            setMediaSource(mediaSourceFactory.createMediaSource(mediaItem))
            prepare()
        }
    }

    /**
     * Parses Kodi InputStream Adaptive license_key format:
     * "<license_url>|<header_query_string>|R{SSM}|R"
     */
    private fun parseKodiLicenseKey(licenseKey: String): Pair<String, Map<String, String>> {
        val parts = licenseKey.split("|")
        val licenseUrl = parts.getOrNull(0).orEmpty()
        val headerStr = parts.getOrNull(1).orEmpty()
        val headers = buildMap {
            if (headerStr.isNotBlank()) {
                for (pair in headerStr.split("&")) {
                    val idx = pair.indexOf("=")
                    if (idx > 0) {
                        val k = URLDecoder.decode(pair.substring(0, idx), "UTF-8")
                        val v = URLDecoder.decode(pair.substring(idx + 1), "UTF-8")
                        put(k, v)
                    }
                }
            }
        }
        return licenseUrl to headers
    }
}
