package com.nufi.keyboard

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject

data class KeyboardSuggestion(
    val word: String,
    val score: Double,
)

data class KeyboardSuggestionResponse(
    val normalizedText: String,
    val usedContext: Int,
    val suggestions: List<KeyboardSuggestion>,
)

class KeyboardApiClient {
    private val client = OkHttpClient()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun fetchSuggestions(
        baseUrl: String,
        text: String,
        n: Int,
        limit: Int,
    ): Result<KeyboardSuggestionResponse> = withContext(Dispatchers.IO) {
        runCatching {
            val payload = JSONObject()
                .put("text", text)
                .put("n", n)
                .put("limit", limit)

            val request = Request.Builder()
                .url("${baseUrl.trimEnd('/')}/api/keyboard/suggest")
                .post(payload.toString().toRequestBody(jsonMediaType))
                .build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    error("Keyboard suggest failed: ${response.code}")
                }

                val body = response.body?.string().orEmpty()
                val json = JSONObject(body)
                parseSuggestionResponse(json)
            }
        }
    }

    private fun parseSuggestionResponse(json: JSONObject): KeyboardSuggestionResponse {
        val suggestionsJson = json.optJSONArray("suggestions") ?: JSONArray()
        val suggestions = buildList {
            for (index in 0 until suggestionsJson.length()) {
                val item = suggestionsJson.getJSONObject(index)
                add(
                    KeyboardSuggestion(
                        word = item.getString("word"),
                        score = item.optDouble("score", 0.0),
                    )
                )
            }
        }

        return KeyboardSuggestionResponse(
            normalizedText = json.optString("normalized_text", ""),
            usedContext = json.optInt("used_context", 0),
            suggestions = suggestions,
        )
    }
}
