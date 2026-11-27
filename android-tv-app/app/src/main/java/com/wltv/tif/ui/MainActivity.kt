package com.wltv.tif.ui

import android.content.Intent
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.wltv.tif.bridge.WltvBridge
import com.wltv.tif.bridge.WltvChannel
import com.wltv.tif.bridge.WltvList
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var statusText: TextView
    private lateinit var listView: ListView
    private var lists: List<WltvList> = emptyList()
    private var channels: List<WltvChannel> = emptyList()
    private var showingChannels = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        statusText = TextView(this).apply {
            text = "Loading WorldLiveTV..."
            textSize = 18f
            setPadding(32, 24, 32, 16)
        }
        listView = ListView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(statusText)
            addView(listView)
        }
        setContentView(layout)

        loadLists()

        listView.setOnItemClickListener { _, _, position, _ ->
            if (!showingChannels) {
                val selected = lists[position]
                loadChannels(selected)
            } else {
                val ch = channels[position]
                startActivity(
                    Intent(this, PlayerActivity::class.java).apply {
                        putExtra("name", ch.name)
                        putExtra("broadcaster", ch.broadcaster)
                        putExtra("channel", ch.channel)
                        putExtra("listName", ch.listName)
                        putExtra("groupId", ch.groupId)
                        putExtra("channelId", ch.channelId)
                    }
                )
            }
        }
    }

    private fun loadLists() {
        lifecycleScope.launch {
            val hotfix = WltvBridge.checkHotfix(this@MainActivity)
            lists = WltvBridge.getRemoteLists(this@MainActivity)
            showingChannels = false
            statusText.text = "WorldLiveTV Lists (hotfix: ${hotfix.optInt("hotfix", 0)})"
            listView.adapter = ArrayAdapter(
                this@MainActivity,
                android.R.layout.simple_list_item_1,
                lists.map { "${it.name} (${it.id})" }
            )
        }
    }

    private fun loadChannels(list: WltvList) {
        statusText.text = "Loading channels: ${list.name}..."
        lifecycleScope.launch {
            try {
                channels = WltvBridge.fetchChannels(this@MainActivity, list.url)
                showingChannels = true
                statusText.text = "${list.name} (${channels.size} channels) - Press Back for lists"
                listView.adapter = ArrayAdapter(
                    this@MainActivity,
                    android.R.layout.simple_list_item_1,
                    channels.map { "[${it.tvgChNo}] ${it.name} (${it.broadcaster})" }
                )
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (showingChannels) {
            loadLists()
        } else {
            super.onBackPressed()
        }
    }
}
