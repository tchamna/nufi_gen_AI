package com.nufi.keyboard

import android.content.Context

class KeyboardSettings(context: Context) {
    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getBaseUrl(): String = prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL

    fun setBaseUrl(baseUrl: String) {
        prefs.edit().putString(KEY_BASE_URL, baseUrl.trim().trimEnd('/')).apply()
    }

    fun getLayoutType(): String = prefs.getString(KEY_LAYOUT_TYPE, LAYOUT_QWERTY) ?: LAYOUT_QWERTY

    fun setLayoutType(layout: String) {
        prefs.edit().putString(KEY_LAYOUT_TYPE, layout).apply()
    }

    companion object {
        const val LAYOUT_QWERTY = "qwerty"
        const val LAYOUT_AZERTY = "azerty"

        private const val PREFS_NAME = "nufi_keyboard_settings"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_LAYOUT_TYPE = "layout_type"
        const val DEFAULT_BASE_URL =
            "https://nufi-gen-ai-dug3ggdsh3fze9e5.canadacentral-01.azurewebsites.net"
    }
}
