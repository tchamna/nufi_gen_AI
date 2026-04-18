package com.nufi.keyboard

import android.content.Context
import java.text.Normalizer
import java.util.Locale

class SuggestionAudioCatalog(context: Context) {
    private val audioByKeyword: Map<String, String> = loadAudioMap(context)

    fun findAudioIdForSuggestion(suggestion: String): String? {
        for (candidate in lookupCandidates(suggestion)) {
            val audioId = audioByKeyword[candidate]
            if (!audioId.isNullOrBlank()) {
                return audioId
            }
        }
        return null
    }

    private fun loadAudioMap(context: Context): Map<String, String> {
        val map = LinkedHashMap<String, String>()
        val exclude = loadExcludeSet(context)
        context.assets.open("nufi_word_list.csv").bufferedReader(Charsets.UTF_8).useLines { lines ->
            lines.drop(1).forEach { line ->
                if (line.isBlank()) return@forEach
                val columns = parseCsvLine(line)
                if (columns.size < 4) return@forEach
                val keyword = normalizeKeyword(columns[2])
                val audioId = columns[3].trim()
                val canonicalKeyword = canonicalLowToneKeyword(keyword)
                if (
                    keyword.isNotEmpty() &&
                    audioId.isNotEmpty() &&
                    !exclude.contains(keyword) &&
                    !exclude.contains(canonicalKeyword)
                ) {
                    map[keyword] = audioId
                    map.putIfAbsent(canonicalKeyword, audioId)
                }
            }
        }
        return map
    }

    private fun loadExcludeSet(context: Context): Set<String> {
        val set = HashSet<String>()
        try {
            context.assets.open("audio_exclude.txt").bufferedReader(Charsets.UTF_8).useLines { lines ->
                lines.forEach { raw ->
                    val n = normalizeKeyword(raw)
                    if (n.isNotEmpty()) set.add(n)
                }
            }
        } catch (e: Exception) {
            // asset may not exist; treat as empty exclude set
        }
        return set
    }

    private fun lookupCandidates(raw: String): List<String> {
        val normalized = normalizeKeyword(raw)
        if (normalized.isEmpty()) return emptyList()
        val candidates = linkedSetOf(normalized)
        val withoutTrailingPunctuation = normalized.trimEnd('.', ',', ';', ':', '!', '?')
        if (withoutTrailingPunctuation.isNotEmpty()) {
            candidates += withoutTrailingPunctuation
            candidates += canonicalLowToneKeyword(withoutTrailingPunctuation)
        }
        candidates += canonicalLowToneKeyword(normalized)
        return candidates.toList()
    }

    private fun normalizeKeyword(raw: String): String {
        val collapsed = raw.trim().replace(Regex("\\s+"), " ")
        if (collapsed.isEmpty()) return ""
        return Normalizer.normalize(collapsed, Normalizer.Form.NFC)
            .lowercase(Locale.ROOT)
            .replace('\u2018', '\'')
            .replace('\u2019', '\'')
    }

    private fun canonicalLowToneKeyword(raw: String): String {
        val normalized = normalizeKeyword(raw)
        if (normalized.isEmpty()) return ""
        val stripped = Normalizer.normalize(normalized, Normalizer.Form.NFD)
            .replace("\u0300", "")
        return Normalizer.normalize(stripped, Normalizer.Form.NFC)
    }

    private fun parseCsvLine(line: String): List<String> {
        val values = mutableListOf<String>()
        val current = StringBuilder()
        var inQuotes = false
        var index = 0

        while (index < line.length) {
            val ch = line[index]
            when {
                ch == '"' && inQuotes && index + 1 < line.length && line[index + 1] == '"' -> {
                    current.append('"')
                    index++
                }
                ch == '"' -> inQuotes = !inQuotes
                ch == ',' && !inQuotes -> {
                    values += current.toString()
                    current.setLength(0)
                }
                else -> current.append(ch)
            }
            index++
        }

        values += current.toString()
        return values
    }
}
