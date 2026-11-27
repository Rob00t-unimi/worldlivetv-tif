package com.wltv.tif.ui

import android.app.Activity
import android.media.tv.TvInputInfo
import android.os.Bundle
import android.widget.ArrayAdapter
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
            text = "Select the WorldLiveTV list to sync with Live Channels"
            textSize = 20f
            setPadding(32, 32, 32, 16)
        }
        val listView = ListView(this)
        val container = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            addView(title)
            addView(listView)
        }
        setContentView(container)

        lifecycleScope.launch {
            WltvBridge.checkHotfix(this@SetupActivity)
            lists = WltvBridge.getRemoteLists(this@SetupActivity)
            val names = lists.map { "${it.name} (${it.id})" }
            listView.adapter = ArrayAdapter(this@SetupActivity, android.R.layout.simple_list_item_1, names)
        }

        listView.setOnItemClickListener { _, _, position, _ ->
            val selected = lists[position]
            val req = OneTimeWorkRequestBuilder<ChannelSyncWorker>()
                .setInputData(
                    workDataOf(
                        ChannelSyncWorker.KEY_INPUT_ID to inputId,
                        ChannelSyncWorker.KEY_LIST_URL to selected.url
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
                }
            }
        }
    }
}
