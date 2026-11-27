package com.wltv.tif.ui

import android.os.Bundle
import android.view.WindowManager
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.wltv.tif.bridge.WltvBridge
import com.wltv.tif.player.ExoPlayerBuilder
import kotlinx.coroutines.launch

class PlayerActivity : AppCompatActivity() {

    private var player: ExoPlayer? = null
    private lateinit var playerView: PlayerView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        playerView = PlayerView(this)
        setContentView(playerView)

        val broadcaster = intent.getStringExtra("broadcaster").orEmpty()
        val channel = intent.getStringExtra("channel").orEmpty()
        val listName = intent.getStringExtra("listName").orEmpty()
        val groupId = intent.getStringExtra("groupId").orEmpty()
        val channelId = intent.getStringExtra("channelId").orEmpty()

        lifecycleScope.launch {
            val resolved = WltvBridge.resolveChannel(
                this@PlayerActivity,
                broadcaster,
                channel,
                listName,
                groupId,
                channelId
            )
            if (resolved.error.isNotBlank() || resolved.url.isBlank()) {
                Toast.makeText(
                    this@PlayerActivity,
                    "Stream error: ${resolved.error.ifBlank { "Empty URL" }}",
                    Toast.LENGTH_LONG
                ).show()
                finish()
                return@launch
            }

            player = ExoPlayerBuilder.buildAndPrepare(this@PlayerActivity, resolved).also {
                playerView.player = it
                it.playWhenReady = true
            }
        }
    }

    override fun onStop() {
        super.onStop()
        player?.release()
        player = null
    }
}
