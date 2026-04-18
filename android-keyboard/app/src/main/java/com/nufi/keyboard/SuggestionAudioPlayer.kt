package com.nufi.keyboard

import android.content.Context
import android.media.MediaPlayer
import android.util.Log
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException
import java.text.Normalizer
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap

class SuggestionAudioPlayer(
    context: Context,
    private val httpClient: OkHttpClient = OkHttpClient(),
) {
    private val appContext = context.applicationContext
    private val resolvedUrlCache = ConcurrentHashMap<String, String>()
    private var mediaPlayer: MediaPlayer? = null

    companion object {
        private const val NOT_FOUND = "NOT_FOUND"
    }

    suspend fun play(baseUrl: String?, word: String?, audioId: String?): Boolean {
        if (baseUrl == null || word == null) {
            Log.e("SuggestionAudioPlayer", "Cannot play: baseUrl or word is null")
            return false
        }
        val url = resolveAudioUrl(baseUrl = baseUrl, word = word, audioId = audioId) ?: return false
        return withContext(Dispatchers.Main) {
            playResolvedUrl(url)
        }
    }

    fun release() {
        mediaPlayer?.release()
        mediaPlayer = null
    }

    private suspend fun resolveAudioUrl(baseUrl: String, word: String, audioId: String?): String? {
        val normalizedWord = normalizeExactAudioWord(word)
        val cacheKey = buildCacheKey(baseUrl = baseUrl, word = normalizedWord, audioId = audioId)
        
        val cached = resolvedUrlCache[cacheKey]
        if (cached != null) {
            Log.d("SuggestionAudioPlayer", "Cache hit for $cacheKey: $cached")
            return if (cached == NOT_FOUND) null else cached
        }

        val candidates = buildCandidateUrls(baseUrl = baseUrl, word = normalizedWord, audioId = audioId)
        Log.d("SuggestionAudioPlayer", "Resolving audio for '$word' (normalized: '$normalizedWord'), candidates: $candidates")
        for (candidate in candidates) {
            if (urlExists(candidate)) {
                Log.d("SuggestionAudioPlayer", "Found valid URL: $candidate")
                try {
                    if (candidate != null) {
                        resolvedUrlCache[cacheKey] = candidate
                    }
                } catch (e: Exception) {
                    Log.w("SuggestionAudioPlayer", "Failed to cache resolved URL for $cacheKey", e)
                }
                return candidate
            }
        }

        Log.d("SuggestionAudioPlayer", "No valid URL found for '$word' after checking ${candidates.size} candidates")
        try {
            resolvedUrlCache[cacheKey] = NOT_FOUND
        } catch (e: Exception) {
            Log.w("SuggestionAudioPlayer", "Failed to cache NOT_FOUND for $cacheKey", e)
        }
        return null
    }

    private fun buildCacheKey(baseUrl: String, word: String, audioId: String?): String {
        return listOf(baseUrl.trimEnd('/'), word.trim(), audioId.orEmpty()).joinToString("|")
    }

    private fun normalizeExactAudioWord(word: String): String {
        return Normalizer.normalize(word, Normalizer.Form.NFC)
            .lowercase(Locale.ROOT)
            .trim()
            .replace('\u2018', '\'')
            .replace('\u2019', '\'')
    }

    private fun buildCandidateUrls(baseUrl: String, word: String, audioId: String?): List<String> {
        val candidates = mutableListOf<String>()
        val encodedWord = Uri.encode(word.trim())
        val trimmedAudioId = audioId?.trim().orEmpty()
        val normalizedBaseUrl = baseUrl.trim().trimEnd('/')
        val query = if (trimmedAudioId.isNotEmpty()) {
            "?audio_id=${Uri.encode(trimmedAudioId)}"
        } else {
            ""
        }

        // 1. Preferred path: same API as suggestions.
        candidates.add("$normalizedBaseUrl/api/audio/$encodedWord$query")

        // 2. Direct S3 fallback if the API route is unavailable.
        candidates.add("https://dictionnaire-nufi-audio.s3.us-east-1.amazonaws.com/$encodedWord.mp3")
        if (trimmedAudioId.isNotEmpty()) {
            val encodedAudioId = Uri.encode(trimmedAudioId)
            candidates.add("https://dictionnaire-nufi-audio.s3.us-east-1.amazonaws.com/$encodedAudioId.mp3")
        }

        return candidates
    }

    private suspend fun urlExists(url: String): Boolean = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url(url)
            .header("User-Agent", "Clafrica-Android-Keyboard/3.0")
            .head()
            .build()
        try {
            httpClient.newCall(request).execute().use { response ->
                Log.d("SuggestionAudioPlayer", "HTTP ${response.code} for $url")
                response.isSuccessful
            }
        } catch (e: Exception) {
            Log.w("SuggestionAudioPlayer", "urlExists failed for $url: ${e.message}")
            false
        }
    }

    private fun playResolvedUrl(url: String): Boolean {
        release()

        Log.d("SuggestionAudioPlayer", "Playing audio from URL: $url")
        val player = MediaPlayer()
        return try {
            player.setDataSource(appContext, Uri.parse(url))
            player.setOnPreparedListener {
                Log.d("SuggestionAudioPlayer", "MediaPlayer prepared, starting playback for $url")
                it.start()
            }
            player.setOnCompletionListener {
                Log.d("SuggestionAudioPlayer", "Playback completed for $url")
                it.release()
                if (mediaPlayer === it) {
                    mediaPlayer = null
                }
            }
            player.setOnErrorListener { mp, what, extra ->
                Log.e("SuggestionAudioPlayer", "MediaPlayer onError for $url: what=$what, extra=$extra")
                mp.release()
                if (mediaPlayer === mp) {
                    mediaPlayer = null
                }
                true
            }
            mediaPlayer = player
            player.prepareAsync()
            true
        } catch (e: Exception) {
            Log.e("SuggestionAudioPlayer", "playResolvedUrl exception for $url", e)
            player.release()
            if (mediaPlayer === player) {
                mediaPlayer = null
            }
            false
        }
    }
}
