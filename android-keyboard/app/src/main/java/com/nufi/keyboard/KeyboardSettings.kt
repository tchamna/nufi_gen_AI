package com.nufi.keyboard

import android.content.Context

class KeyboardSettings(context: Context) {
    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getBaseUrl(): String = prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL

    fun setBaseUrl(baseUrl: String) {
        prefs.edit().putString(KEY_BASE_URL, baseUrl.trim().trimEnd('/')).apply()
    }

    companion object {
        private const val PREFS_NAME = "nufi_keyboard_settings"
        private const val KEY_BASE_URL = "base_url"
        const val DEFAULT_BASE_URL =
            "https://nufi-gen-ai-dug3ggdsh3fze9e5.canadacentral-01.azurewebsites.net"
    }
}
