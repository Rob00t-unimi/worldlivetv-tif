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
        val listUrl = inputData.getString(KEY_LIST_URL) ?: return Result.failure()

        return try {
            WltvBridge.checkHotfix(applicationContext)
            val channels = WltvBridge.fetchChannels(applicationContext, listUrl)
            val resolver = applicationContext.contentResolver

            // Clear existing channels (and cascade-deleted programs) for this input
            resolver.delete(
                TvContractCompat.buildChannelsUriForInput(inputId),
                null,
                null
            )

            val insertedIdsByTvgId = HashMap<String, Long>()

            channels.forEachIndexed { index, ch ->
                val providerData = JSONObject().apply {
                    put("broadcaster", ch.broadcaster)
                    put("channel", ch.channel)
                    put("listName", ch.listName)
                    put("groupId", ch.groupId)
                    put("channelId", ch.channelId)
                    put("tvgId", ch.tvgId)
                }.toString().toByteArray(Charsets.UTF_8)

                val displayNum = ch.tvgChNo.ifBlank { (index + 1).toString() }
                val values = ContentValues().apply {
                    put(TvContract.Channels.COLUMN_INPUT_ID, inputId)
                    put(TvContract.Channels.COLUMN_DISPLAY_NUMBER, displayNum)
                    put(TvContract.Channels.COLUMN_DISPLAY_NAME, ch.name)
                    put(TvContract.Channels.COLUMN_ORIGINAL_NETWORK_ID, index + 1)
                    put(TvContract.Channels.COLUMN_TYPE, TvContract.Channels.TYPE_OTHER)
                    put(TvContract.Channels.COLUMN_SERVICE_TYPE, TvContract.Channels.SERVICE_TYPE_AUDIO_VIDEO)
                    put(TvContract.Channels.COLUMN_INTERNAL_PROVIDER_DATA, providerData)
                }
                val uri = resolver.insert(TvContract.Channels.CONTENT_URI, values)
                if (uri != null && ch.tvgId.isNotBlank()) {
                    insertedIdsByTvgId[ch.tvgId] = ContentUris.parseId(uri)
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

            Result.success(workDataOf(KEY_COUNT to channels.size))
        } catch (e: Exception) {
            Result.failure(workDataOf(KEY_ERROR to (e.message ?: "Unknown sync error")))
        }
    }

    companion object {
        const val KEY_INPUT_ID = "input_id"
        const val KEY_LIST_URL = "list_url"
        const val KEY_COUNT = "count"
        const val KEY_ERROR = "error"
    }
}
