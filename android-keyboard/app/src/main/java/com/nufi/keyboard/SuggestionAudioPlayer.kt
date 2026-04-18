package com.nufi.keyboard

import android.content.Context
import android.media.MediaPlayer
import android.net.Uri
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.suspendCancellableCoroutine
import java.text.Normalizer
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import kotlin.coroutines.resume

class SuggestionAudioPlayer(
    context: Context,
) {
    private val appContext = context.applicationContext
    private val resolvedUrlCache = ConcurrentHashMap<String, String>()
    private var mediaPlayer: MediaPlayer? = null

    suspend fun play(baseUrl: String?, word: String?, audioId: String?): Boolean {
        if (baseUrl == null || word == null) {
            Log.e("SuggestionAudioPlayer", "Cannot play: baseUrl or word is null")
            return false
        }
        return withContext(Dispatchers.Main) {
            playResolvedAudio(baseUrl = baseUrl, word = word, audioId = audioId)
        }
    }

    fun release() {
        mediaPlayer?.release()
        mediaPlayer = null
    }

    private suspend fun playResolvedAudio(baseUrl: String, word: String, audioId: String?): Boolean {
        val normalizedWord = normalizeExactAudioWord(word)
        val cacheKey = buildCacheKey(baseUrl = baseUrl, word = normalizedWord, audioId = audioId)
        val cached = resolvedUrlCache[cacheKey]
        val candidates = buildCandidateUrls(baseUrl = baseUrl, word = normalizedWord, audioId = audioId)
        val orderedCandidates =
            if (cached != null && candidates.contains(cached)) {
                listOf(cached) + candidates.filterNot { it == cached }
            } else {
                candidates
            }

        Log.d(
            "SuggestionAudioPlayer",
            "Playing audio for '$word' (normalized: '$normalizedWord'), candidates: $orderedCandidates",
        )
        for (candidate in orderedCandidates) {
            if (playResolvedUrl(candidate)) {
                resolvedUrlCache[cacheKey] = candidate
                return true
            }
        }

        Log.d("SuggestionAudioPlayer", "No playable audio found for '$word'")
        return false
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

    private suspend fun playResolvedUrl(url: String): Boolean = suspendCancellableCoroutine { continuation ->
        release()

        Log.d("SuggestionAudioPlayer", "Playing audio from URL: $url")
        val player = MediaPlayer()
        try {
            player.setDataSource(appContext, Uri.parse(url))
            player.setOnPreparedListener {
                Log.d("SuggestionAudioPlayer", "MediaPlayer prepared, starting playback for $url")
                it.start()
                if (continuation.isActive) {
                    continuation.resume(true)
                }
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
                if (continuation.isActive) {
                    continuation.resume(false)
                }
                true
            }
            mediaPlayer = player
            continuation.invokeOnCancellation {
                player.release()
                if (mediaPlayer === player) {
                    mediaPlayer = null
                }
            }
            player.prepareAsync()
        } catch (e: Exception) {
            Log.e("SuggestionAudioPlayer", "playResolvedUrl exception for $url", e)
            player.release()
            if (mediaPlayer === player) {
                mediaPlayer = null
            }
            if (continuation.isActive) {
                continuation.resume(false)
            }
        }
    }
}
