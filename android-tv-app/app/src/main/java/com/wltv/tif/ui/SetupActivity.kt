package com.wltv.tif.ui

import android.app.Activity
import android.media.tv.TvInputInfo
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkInfo
import androidx.work.WorkManager
import androidx.work.workDataOf
import java.util.concurrent.TimeUnit
import com.wltv.tif.bridge.WltvBridge
import com.wltv.tif.bridge.WltvList
import com.wltv.tif.sync.ChannelBlacklist
import com.wltv.tif.sync.ChannelSyncWorker
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

class SetupActivity : AppCompatActivity() {

    private var lists: List<WltvList> = emptyList()
    private var inputId: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        inputId = intent.getStringExtra(TvInputInfo.EXTRA_INPUT_ID).orEmpty()

        val title = TextView(this).apply {
            text = "Select WorldLiveTV lists to sync"
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
        val filterCheckBox = CheckBox(this).apply {
            text = "Filter out offline/empty channels before adding"
            isChecked = true
            setPadding(16, 8, 16, 8)
        }
        val syncButton = Button(this).apply {
            text = "Sync Selected Lists"
            isEnabled = false
        }
        val resetHiddenButton = Button(this).apply {
            val hiddenCount = ChannelBlacklist.count(this@SetupActivity)
            text = "Restore Hidden Channels ($hiddenCount)"
            isEnabled = hiddenCount > 0
            setOnClickListener {
                ChannelBlacklist.clearAll(this@SetupActivity)
                text = "Restore Hidden Channels (0)"
                isEnabled = false
                Toast.makeText(this@SetupActivity, "Hidden channels cleared", Toast.LENGTH_SHORT).show()
            }
        }

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(title)
            addView(listView)
            addView(filterCheckBox)
            addView(syncButton)
            addView(resetHiddenButton)
        }
        setContentView(container)

        // Show cached lists immediately so UI is instant even if a background sync is running
        val cachedLists = loadCachedLists()
        if (cachedLists.isNotEmpty()) {
            applyListsToUi(cachedLists, listView, syncButton)
        } else {
            title.text = "Loading WorldLiveTV lists..."
        }

        lifecycleScope.launch {
            runCatching {
                val fresh = WltvBridge.getRemoteLists(this@SetupActivity)
                if (fresh.isNotEmpty()) {
                    saveCachedLists(fresh)
                    if (lists.isEmpty()) {
                        title.text = "Select WorldLiveTV lists to sync"
                        applyListsToUi(fresh, listView, syncButton)
                    }
                }
            }
        }

        syncButton.setOnClickListener {
            val checked = listView.checkedItemPositions
            val selectedUrls = ArrayList<String>()
            val selectedIds = ArrayList<String>()
            for (i in lists.indices) {
                if (checked.get(i)) {
                    selectedUrls.add(lists[i].url)
                    selectedIds.add(lists[i].id)
                }
            }
            if (selectedUrls.isEmpty()) {
                Toast.makeText(this, "Select at least one list", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            syncButton.isEnabled = false
            syncButton.text = if (filterCheckBox.isChecked) "Checking & Syncing (please wait)..." else "Syncing..."

            val syncData = workDataOf(
                ChannelSyncWorker.KEY_INPUT_ID to inputId,
                ChannelSyncWorker.KEY_LIST_URLS to selectedUrls.toTypedArray(),
                ChannelSyncWorker.KEY_LIST_IDS to selectedIds.toTypedArray(),
                ChannelSyncWorker.KEY_FILTER_OFFLINE to filterCheckBox.isChecked
            )

            val req = OneTimeWorkRequestBuilder<ChannelSyncWorker>()
                .setInputData(syncData)
                .build()

            val wm = WorkManager.getInstance(this)
            wm.enqueue(req)

            // Also schedule automatic 12-hour background sync for channels + EPG
            val periodicReq = PeriodicWorkRequestBuilder<ChannelSyncWorker>(12, TimeUnit.HOURS)
                .setInputData(syncData)
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .build()
            wm.enqueueUniquePeriodicWork(
                "wltv_auto_sync",
                ExistingPeriodicWorkPolicy.UPDATE,
                periodicReq
            )
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

    private fun applyListsToUi(items: List<WltvList>, listView: ListView, syncButton: Button) {
        lists = items
        val names = lists.map { it.name }
        listView.adapter = ArrayAdapter(
            this,
            android.R.layout.simple_list_item_multiple_choice,
            names
        )
        val dttIndex = lists.indexOfFirst { it.id == "_dtt_kodi" }
        if (dttIndex >= 0) {
            listView.setItemChecked(dttIndex, true)
        }
        syncButton.isEnabled = lists.isNotEmpty()
    }

    private fun saveCachedLists(items: List<WltvList>) {
        val arr = JSONArray()
        for (item in items) {
            arr.put(JSONObject().apply {
                put("id", item.id)
                put("name", item.name)
                put("type", item.type)
                put("url", item.url)
                put("epg", item.epg)
            })
        }
        getSharedPreferences("wltv_setup_cache", MODE_PRIVATE)
            .edit()
            .putString("lists_json", arr.toString())
            .apply()
    }

    private fun loadCachedLists(): List<WltvList> {
        val raw = getSharedPreferences("wltv_setup_cache", MODE_PRIVATE)
            .getString("lists_json", null) ?: return emptyList()
        return runCatching {
            val arr = JSONArray(raw)
            buildList {
                for (i in 0 until arr.length()) {
                    val obj = arr.getJSONObject(i)
                    add(
                        WltvList(
                            id = obj.optString("id"),
                            name = obj.optString("name"),
                            type = obj.optString("type"),
                            url = obj.optString("url"),
                            epg = obj.optString("epg")
                        )
                    )
                }
            }
        }.getOrDefault(emptyList())
    }
}
