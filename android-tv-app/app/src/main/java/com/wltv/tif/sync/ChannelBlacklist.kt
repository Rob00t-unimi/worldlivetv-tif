package com.wltv.tif.sync

import android.content.Context

object ChannelBlacklist {
    private const val PREFS_NAME = "wltv_blacklist"
    private const val KEY_HIDDEN = "hidden_channels"

    fun keyFor(broadcaster: String, channel: String, channelId: String = ""): String {
        return "$broadcaster|$channel|$channelId"
    }

    fun isHidden(context: Context, key: String): Boolean {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val set = prefs.getStringSet(KEY_HIDDEN, emptySet()) ?: emptySet()
        return set.contains(key)
    }

    fun hide(context: Context, key: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val current = HashSet(prefs.getStringSet(KEY_HIDDEN, emptySet()) ?: emptySet())
        if (current.add(key)) {
            prefs.edit().putStringSet(KEY_HIDDEN, current).apply()
        }
    }

    fun clearAll(context: Context) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .remove(KEY_HIDDEN)
            .apply()
    }

    fun count(context: Context): Int {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getStringSet(KEY_HIDDEN, emptySet())?.size ?: 0
    }
}
