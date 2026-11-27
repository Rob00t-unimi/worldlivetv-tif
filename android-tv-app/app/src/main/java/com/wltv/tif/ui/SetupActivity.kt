package com.wltv.tif.ui

import android.app.Activity
import android.media.tv.TvInputInfo
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkInfo
import androidx.work.WorkManager
import androidx.work.workDataOf
import com.wltv.tif.bridge.WltvBridge
import com.wltv.tif.bridge.WltvList
import com.wltv.tif.sync.ChannelSyncWorker
import kotlinx.coroutines.launch

class SetupActivity : AppCompatActivity() {

    private var lists: List<WltvList> = emptyList()
    private var inputId: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        inputId = intent.getStringExtra(TvInputInfo.EXTRA_INPUT_ID).orEmpty()

        val title = TextView(this).apply {
            text = "Select one or more WorldLiveTV lists to sync with Live Channels"
            textSize = 20f
            setPadding(32, 24, 32, 12)
        }
        val listView = ListView(this).apply {
            choiceMode = ListView.CHOICE_MODE_MULTIPLE
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        }
        val syncButton = Button(this).apply {
            text = "Sync Selected Lists"
            isEnabled = false
        }

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(title)
            addView(listView)
            addView(syncButton)
        }
        setContentView(container)

        lifecycleScope.launch {
            WltvBridge.checkHotfix(this@SetupActivity)
            lists = WltvBridge.getRemoteLists(this@SetupActivity)
            val names = lists.map { "${it.name} (${it.id})" }
            listView.adapter = ArrayAdapter(
                this@SetupActivity,
                android.R.layout.simple_list_item_multiple_choice,
                names
            )
            // Pre-select DTT by default if present
            val dttIndex = lists.indexOfFirst { it.id == "_dtt_kodi" }
            if (dttIndex >= 0) {
                listView.setItemChecked(dttIndex, true)
            }
            syncButton.isEnabled = lists.isNotEmpty()
        }

        syncButton.setOnClickListener {
            val checked = listView.checkedItemPositions
            val selectedUrls = ArrayList<String>()
            for (i in lists.indices) {
                if (checked.get(i)) {
                    selectedUrls.add(lists[i].url)
                }
            }
            if (selectedUrls.isEmpty()) {
                Toast.makeText(this, "Select at least one list", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            syncButton.isEnabled = false
            syncButton.text = "Syncing..."

            val req = OneTimeWorkRequestBuilder<ChannelSyncWorker>()
                .setInputData(
                    workDataOf(
                        ChannelSyncWorker.KEY_INPUT_ID to inputId,
                        ChannelSyncWorker.KEY_LIST_URLS to selectedUrls.toTypedArray()
                    )
                )
                .build()

            val wm = WorkManager.getInstance(this)
            wm.enqueue(req)
            wm.getWorkInfoByIdLiveData(req.id).observe(this) { info ->
                if (info?.state == WorkInfo.State.SUCCEEDED) {
                    val count = info.outputData.getInt(ChannelSyncWorker.KEY_COUNT, 0)
                    Toast.makeText(this, "Synced $count channels", Toast.LENGTH_SHORT).show()
                    setResult(Activity.RESULT_OK)
                    finish()
                } else if (info?.state == WorkInfo.State.FAILED) {
                    val err = info.outputData.getString(ChannelSyncWorker.KEY_ERROR)
                    Toast.makeText(this, "Sync error: $err", Toast.LENGTH_LONG).show()
                    syncButton.isEnabled = true
                    syncButton.text = "Sync Selected Lists"
                }
            }
        }
    }
}
