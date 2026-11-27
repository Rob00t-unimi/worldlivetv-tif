package com.wltv.tif.bridge

import android.content.Context
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

data class WltvList(
    val id: String,
    val name: String,
    val type: String,
    val url: String,
    val epg: String
)

data class WltvChannel(
    val name: String,
    val tvgId: String,
    val tvgLogo: String,
    val tvgChNo: String,
    val group: String,
    val broadcaster: String,
    val channel: String,
    val listName: String = "",
    val groupId: String = "",
    val channelId: String = ""
)

data class EpgProgram(
    val title: String,
    val desc: String,
    val startMs: Long,
    val stopMs: Long
)

data class ResolvedStream(
    val title: String,
    val url: String,
    val manifestType: String,
    val licenseKey: String,
    val streamHeaders: Map<String, String>,
    val manifestHeaders: Map<String, String>,
    val error: String = ""
)

object WltvBridge {
    @Volatile
    private var initialized = false

    private fun getModule(context: Context): PyObject {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(context.applicationContext))
        }
        val py = Python.getInstance()
        val module = py.getModule("wltv_bridge")
        if (!initialized) {
            synchronized(this) {
                if (!initialized) {
                    val dataDir = File(context.filesDir, "wltv_data").apply { mkdirs() }.absolutePath
                    module.callAttr("init", dataDir, "")
                    initialized = true
                }
            }
        }
        return module
    }

    suspend fun checkHotfix(context: Context): JSONObject = withContext(Dispatchers.IO) {
        val res = getModule(context).callAttr("check_hotfix").toString()
        JSONObject(res)
    }

    suspend fun getRemoteLists(context: Context): List<WltvList> = withContext(Dispatchers.IO) {
        val raw = getModule(context).callAttr("get_remote_lists").toString()
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
    }

    suspend fun fetchChannels(
        context: Context,
        m3uUrl: String,
        filterOffline: Boolean = false
    ): List<WltvChannel> = withContext(Dispatchers.IO) {
        val mod = getModule(context)
        var raw = mod.callAttr("fetch_m3u_channels", m3uUrl).toString()
        if (filterOffline) {
            raw = mod.callAttr("filter_working_channels", raw, 16).toString()
        }
        val arr = JSONArray(raw)
        buildList {
            for (i in 0 until arr.length()) {
                val obj = arr.getJSONObject(i)
                add(
                    WltvChannel(
                        name = obj.optString("name"),
                        tvgId = obj.optString("tvgId"),
                        tvgLogo = obj.optString("tvgLogo"),
                        tvgChNo = obj.optString("tvgChNo"),
                        group = obj.optString("group"),
                        broadcaster = obj.optString("broadcaster"),
                        channel = obj.optString("channel"),
                        listName = obj.optString("listName"),
                        groupId = obj.optString("groupId"),
                        channelId = obj.optString("channelId")
                    )
                )
            }
        }
    }

    suspend fun fetchEpgPrograms(
        context: Context,
        channelIds: List<String>,
        maxPerChannel: Int = 20
    ): Map<String, List<EpgProgram>> = withContext(Dispatchers.IO) {
        if (channelIds.isEmpty()) return@withContext emptyMap()
        val idsJson = JSONArray(channelIds).toString()
        val raw = getModule(context).callAttr("fetch_epg_programs", idsJson, maxPerChannel).toString()
        val root = JSONObject(raw)
        buildMap {
            val keys = root.keys()
            while (keys.hasNext()) {
                val chId = keys.next()
                val arr = root.getJSONArray(chId)
                val list = buildList {
                    for (i in 0 until arr.length()) {
                        val p = arr.getJSONObject(i)
                        add(
                            EpgProgram(
                                title = p.optString("title"),
                                desc = p.optString("desc"),
                                startMs = p.optLong("startMs"),
                                stopMs = p.optLong("stopMs")
                            )
                        )
                    }
                }
                put(chId, list)
            }
        }
    }

    suspend fun resolveChannel(
        context: Context,
        broadcaster: String,
        channel: String,
        listName: String = "",
        groupId: String = "",
        channelId: String = ""
    ): ResolvedStream = withContext(Dispatchers.IO) {
        val raw = getModule(context).callAttr(
            "resolve_channel",
            broadcaster,
            channel,
            listName,
            groupId,
            channelId
        ).toString()
        val obj = JSONObject(raw)
        ResolvedStream(
            title = obj.optString("title"),
            url = obj.optString("url"),
            manifestType = obj.optString("manifestType", "hls"),
            licenseKey = obj.optString("licenseKey"),
            streamHeaders = obj.optJSONObject("streamHeaders")?.toMap() ?: emptyMap(),
            manifestHeaders = obj.optJSONObject("manifestHeaders")?.toMap() ?: emptyMap(),
            error = obj.optString("error")
        )
    }

    private fun JSONObject.toMap(): Map<String, String> = buildMap {
        val keys = keys()
        while (keys.hasNext()) {
            val k = keys.next()
            put(k, optString(k))
        }
    }
}
