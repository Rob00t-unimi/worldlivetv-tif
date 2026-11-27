package com.wltv.tif.sync

import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.media.tv.TvContract
import androidx.tvprovider.media.tv.TvContractCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.wltv.tif.bridge.WltvBridge
import org.json.JSONObject

class ChannelSyncWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val inputId = inputData.getString(KEY_INPUT_ID) ?: return Result.failure()
        val listUrls = inputData.getStringArray(KEY_LIST_URLS)?.toList()
            ?: inputData.getString(KEY_LIST_URL)?.let { listOf(it) }
            ?: return Result.failure()
        val listIds = inputData.getStringArray(KEY_LIST_IDS)?.toList()
            ?: List(listUrls.size) { "" }

        return try {
            WltvBridge.checkHotfix(applicationContext)

            val resolver = applicationContext.contentResolver
            resolver.delete(
                TvContractCompat.buildChannelsUriForInput(inputId),
                null,
                null
            )

            val insertedIdsByTvgId = HashMap<String, Long>()
            var totalInserted = 0
            var otherBlockIdx = 0

            for (i in listUrls.indices) {
                val url = listUrls[i]
                if (url.isBlank()) continue

                val listId = listIds.getOrElse(i) { "" }
                val baseOffset = sectionOffsetFor(listId) {
                    5000 + (otherBlockIdx++ * 1000)
                }

                val channels = WltvBridge.fetchChannels(applicationContext, url)
                var localIdx = 0

                for (ch in channels) {
                    val key = ChannelBlacklist.keyFor(ch.broadcaster, ch.channel, ch.channelId)
                    if (ChannelBlacklist.isHidden(applicationContext, key)) {
                        continue
                    }

                    localIdx++
                    val displayNum = computeDisplayNumber(listId, baseOffset, localIdx, ch.tvgChNo)

                    val providerData = JSONObject().apply {
                        put("broadcaster", ch.broadcaster)
                        put("channel", ch.channel)
                        put("listName", ch.listName)
                        put("groupId", ch.groupId)
                        put("channelId", ch.channelId)
                        put("tvgId", ch.tvgId)
                    }.toString().toByteArray(Charsets.UTF_8)

                    val values = ContentValues().apply {
                        put(TvContract.Channels.COLUMN_INPUT_ID, inputId)
                        put(TvContract.Channels.COLUMN_DISPLAY_NUMBER, displayNum)
                        put(TvContract.Channels.COLUMN_DISPLAY_NAME, ch.name)
                        put(TvContract.Channels.COLUMN_ORIGINAL_NETWORK_ID, baseOffset + localIdx)
                        put(TvContract.Channels.COLUMN_TYPE, TvContract.Channels.TYPE_OTHER)
                        put(TvContract.Channels.COLUMN_SERVICE_TYPE, TvContract.Channels.SERVICE_TYPE_AUDIO_VIDEO)
                        put(TvContract.Channels.COLUMN_BROWSABLE, 1)
                        put(TvContract.Channels.COLUMN_INTERNAL_PROVIDER_DATA, providerData)
                    }
                    val uri = resolver.insert(TvContract.Channels.CONTENT_URI, values)
                    if (uri != null) {
                        totalInserted++
                        if (ch.tvgId.isNotBlank()) {
                            insertedIdsByTvgId[ch.tvgId] = ContentUris.parseId(uri)
                        }
                    }
                }
            }

            // Sync EPG programs from wltv.xz
            if (insertedIdsByTvgId.isNotEmpty()) {
                val epgMap = runCatching {
                    WltvBridge.fetchEpgPrograms(applicationContext, insertedIdsByTvgId.keys.toList())
                }.getOrDefault(emptyMap())

                val programValues = ArrayList<ContentValues>()
                for ((tvgId, dbChannelId) in insertedIdsByTvgId) {
                    val progs = epgMap[tvgId].orEmpty()
                    for (prog in progs) {
                        programValues.add(
                            ContentValues().apply {
                                put(TvContract.Programs.COLUMN_CHANNEL_ID, dbChannelId)
                                put(TvContract.Programs.COLUMN_TITLE, prog.title)
                                put(TvContract.Programs.COLUMN_SHORT_DESCRIPTION, prog.desc)
                                put(TvContract.Programs.COLUMN_START_TIME_UTC_MILLIS, prog.startMs)
                                put(TvContract.Programs.COLUMN_END_TIME_UTC_MILLIS, prog.stopMs)
                            }
                        )
                    }
                }
                if (programValues.isNotEmpty()) {
                    resolver.bulkInsert(TvContract.Programs.CONTENT_URI, programValues.toTypedArray())
                }
            }

            Result.success(workDataOf(KEY_COUNT to totalInserted))
        } catch (e: Exception) {
            Result.failure(workDataOf(KEY_ERROR to (e.message ?: "Unknown sync error")))
        }
    }

    private inline fun sectionOffsetFor(listId: String, nextOtherOffset: () -> Int): Int {
        val id = listId.lowercase()
        return when {
            id == "_dtt_kodi" -> 0
            id.contains("regional") -> 1000
            id.contains("pluto") -> 2000
            id.contains("samsung") -> 3000
            id.contains("rakuten") -> 4000
            id.contains("radio") -> 9000
            else -> nextOtherOffset()
        }
    }

    private fun computeDisplayNumber(
        listId: String,
        baseOffset: Int,
        localIdx: Int,
        tvgChNo: String
    ): String {
        if (listId.equals("_dtt_kodi", ignoreCase = true)) {
            val lcn = tvgChNo.toIntOrNull()
            if (lcn != null && lcn in 1..999) {
                return lcn.toString()
            }
        }
        return (baseOffset + localIdx).toString()
    }

    companion object {
        const val KEY_INPUT_ID = "input_id"
        const val KEY_LIST_URL = "list_url"
        const val KEY_LIST_URLS = "list_urls"
        const val KEY_LIST_IDS = "list_ids"
        const val KEY_COUNT = "count"
        const val KEY_ERROR = "error"
    }
}
