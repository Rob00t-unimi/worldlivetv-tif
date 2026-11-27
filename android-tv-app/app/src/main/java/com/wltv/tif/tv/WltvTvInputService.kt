package com.wltv.tif.tv

import android.content.ContentValues
import android.content.Context
import android.media.tv.TvContract
import android.media.tv.TvInputManager
import android.media.tv.TvInputService
import android.net.Uri
import android.view.Surface
import androidx.annotation.OptIn
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import com.wltv.tif.bridge.WltvBridge
import com.wltv.tif.player.ExoPlayerBuilder
import com.wltv.tif.sync.ChannelBlacklist
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import org.json.JSONObject

class WltvTvInputService : TvInputService() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        serviceScope.launch {
            runCatching { WltvBridge.checkHotfix(applicationContext) }
        }
    }

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
    }

    override fun onCreateSession(inputId: String): Session {
        return WltvSession(this)
    }

    private class WltvSession(private val context: Context) : Session(context) {
        private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        private var tuneJob: Job? = null
        private var player: ExoPlayer? = null
        private var currentSurface: Surface? = null
        private var currentVolume: Float = 1.0f
        private var currentChannelUri: Uri? = null
        private var currentChannelKey: String? = null

        override fun onRelease() {
            tuneJob?.cancel()
            scope.cancel()
            player?.release()
            player = null
        }

        override fun onSetSurface(surface: Surface?): Boolean {
            currentSurface = surface
            player?.setVideoSurface(surface)
            return true
        }

        override fun onSetStreamVolume(volume: Float) {
            currentVolume = volume
            player?.volume = volume
        }

        @OptIn(UnstableApi::class)
        override fun onTune(channelUri: Uri): Boolean {
            currentChannelUri = channelUri
            notifyVideoUnavailable(TvInputManager.VIDEO_UNAVAILABLE_REASON_TUNING)
            tuneJob?.cancel()
            tuneJob = scope.launch {
                val meta = loadChannelMeta(channelUri)
                if (meta == null) {
                    notifyVideoUnavailable(TvInputManager.VIDEO_UNAVAILABLE_REASON_UNKNOWN)
                    return@launch
                }

                val broadcaster = meta.optString("broadcaster")
                val channel = meta.optString("channel")
                val listName = meta.optString("listName")
                val groupId = meta.optString("groupId")
                val channelId = meta.optString("channelId")
                currentChannelKey = ChannelBlacklist.keyFor(broadcaster, channel, channelId)

                val resolved = WltvBridge.resolveChannel(
                    context = context,
                    broadcaster = broadcaster,
                    channel = channel,
                    listName = listName,
                    groupId = groupId,
                    channelId = channelId
                )

                if (resolved.error.isNotBlank() || resolved.url.isBlank()) {
                    markCurrentChannelBroken()
                    notifyVideoUnavailable(TvInputManager.VIDEO_UNAVAILABLE_REASON_UNKNOWN)
                    return@launch
                }

                val mediaSource = ExoPlayerBuilder.buildMediaSource(resolved)
                val exo = getOrCreatePlayer()
                exo.stop()
                exo.setMediaSource(mediaSource)
                exo.prepare()
                exo.playWhenReady = true
            }
            return true
        }

        override fun onSetCaptionEnabled(enabled: Boolean) {
            // Subtitles can be toggled here via ExoPlayer track selection parameters
        }

        @OptIn(UnstableApi::class)
        private fun getOrCreatePlayer(): ExoPlayer {
            return player ?: ExoPlayerBuilder.createFastPlayer(context).apply {
                setVideoSurface(currentSurface)
                volume = currentVolume
                addListener(object : Player.Listener {
                    override fun onPlaybackStateChanged(playbackState: Int) {
                        if (playbackState == Player.STATE_READY) {
                            notifyVideoAvailable()
                        } else if (playbackState == Player.STATE_BUFFERING) {
                            notifyVideoUnavailable(TvInputManager.VIDEO_UNAVAILABLE_REASON_BUFFERING)
                        }
                    }

                    override fun onPlayerError(error: PlaybackException) {
                        markCurrentChannelBroken()
                        notifyVideoUnavailable(TvInputManager.VIDEO_UNAVAILABLE_REASON_UNKNOWN)
                    }
                })
                player = this
            }
        }

        private fun markCurrentChannelBroken() {
            val key = currentChannelKey ?: return
            val uri = currentChannelUri ?: return
            ChannelBlacklist.hide(context, key)
            scope.launch(Dispatchers.IO) {
                runCatching {
                    context.contentResolver.delete(uri, null, null)
                }
            }
        }

        private fun loadChannelMeta(channelUri: Uri): JSONObject? {
            val projection = arrayOf(TvContract.Channels.COLUMN_INTERNAL_PROVIDER_DATA)
            context.contentResolver.query(channelUri, projection, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val blob = cursor.getBlob(0) ?: return null
                    return JSONObject(String(blob, Charsets.UTF_8))
                }
            }
            return null
        }
    }
}
