package com.nufi.keyboard

import android.content.Context
import org.json.JSONObject
import java.time.LocalDate
import java.util.Locale
import java.util.regex.Pattern

/**
 * Mirrors [clafricaMapping.ts], overlays SMS shortcuts from [assets/nufi_sms.json],
 * and resolves calendar dates from [assets/nufi_calendar.json].
 */
class ClafricaEngine(context: Context) {

    private val tokenMap: Map<String, String>
    private val phraseMap: Map<String, String>
    private val calendarMap: Map<String, String>
    private val allKeysSorted: List<String>
    private val phrasePatternsSorted: List<Pair<Regex, String>>
    private val ambiguousKeys: Set<String>
    private val calendarPattern = Regex("(?<![\\p{L}\\p{N}])(\\d{1,2})([ -])(\\d{1,2})\\2(\\d{4})(?![\\p{L}\\p{N}])")
    private val todayKeywords = setOf("today*", "aujourd'hui*", "aujourdhui*", "date*", "l'nz")

    init {
        val tokenEntries = LinkedHashMap<String, String>()
        val phraseEntries = LinkedHashMap<String, String>()
        loadAssetMap(context, "clafrica.json", tokenEntries, phraseEntries)
        loadAssetMap(context, "nufi_sms.json", tokenEntries, phraseEntries)
        tokenMap = tokenEntries
        phraseMap = phraseEntries
        calendarMap = loadJsonAsset(context, "nufi_calendar.json")
        allKeysSorted = tokenMap.keys.sortedWith(compareBy<String> { -it.length }.thenBy { it })
        phrasePatternsSorted = phraseMap.keys
            .sortedWith(compareBy<String> { -it.length }.thenBy { it })
            .map { key ->
                Regex("(?<![\\p{L}\\p{N}])${Regex.escape(key)}(?![\\p{L}\\p{N}])") to phraseMap.getValue(key)
            }
        ambiguousKeys = allKeysSorted.filter { key ->
            allKeysSorted.any { other -> other.length > key.length && other.startsWith(key) }
        }.toSet()
    }

    private fun loadJsonAsset(context: Context, assetName: String): LinkedHashMap<String, String> {
        val jsonText = context.assets.open(assetName).bufferedReader(Charsets.UTF_8).use { it.readText() }
        val json = JSONObject(jsonText)
        val destination = LinkedHashMap<String, String>()
        val keys = json.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            destination[key] = json.getString(key)
        }
        return destination
    }

    private fun loadAssetMap(
        context: Context,
        assetName: String,
        tokenDestination: MutableMap<String, String>,
        phraseDestination: MutableMap<String, String>,
    ) {
        val assetMap = loadJsonAsset(context, assetName)
        for ((key, value) in assetMap) {
            if (key.any { it.isWhitespace() }) {
                phraseDestination[key] = value
            } else {
                tokenDestination[key] = value
            }
        }
    }

    fun applyClafricaMapping(input: String, preserveAmbiguousTrailingToken: Boolean): String {
        if (input.isEmpty()) return input
        val sequenceMapped = applyPhraseMappings(applyCalendarMappings(input))
        val segments = splitWithWhitespace(sequenceMapped)
        val trailingTokenIndex = if (!hasTrailingWhitespace(input)) segments.size - 1 else -1
        return segments.mapIndexed { index, segment ->
            when {
                segment.matches(Regex("\\s+")) -> segment
                preserveAmbiguousTrailingToken && index == trailingTokenIndex -> applyLiveClafricaMappingToTrailingToken(segment)
                else -> applyClafricaMappingToToken(segment)
            }
        }.joinToString("")
    }

    fun finalizeClafricaInput(input: String): String {
        if (input.isEmpty()) return input
        val sequenceMapped = applyPhraseMappings(applyCalendarMappings(input))
        return splitWithWhitespace(sequenceMapped).joinToString("") { segment ->
            if (segment.matches(Regex("\\s+"))) segment else finalizeClafricaToken(segment)
        }
    }

    private fun applyCalendarMappings(input: String): String {
        if (calendarMap.isEmpty() || input.isEmpty()) return input
        return calendarPattern.replace(input) { match ->
            val day = match.groupValues[1].toIntOrNull() ?: return@replace match.value
            val month = match.groupValues[3].toIntOrNull() ?: return@replace match.value
            val year = match.groupValues[4].toIntOrNull() ?: return@replace match.value
            val canonical = String.format(Locale.ROOT, "%02d-%02d-%04d", day, month, year)
            calendarMap[canonical] ?: match.value
        }
    }

    private fun applyPhraseMappings(input: String): String {
        if (phrasePatternsSorted.isEmpty() || input.isEmpty()) return input
        var result = input
        var changed = true
        while (changed) {
            changed = false
            for ((pattern, replacement) in phrasePatternsSorted) {
                val newResult = pattern.replace(result, replacement)
                if (newResult != result) {
                    result = newResult
                    changed = true
                    break
                }
            }
        }
        return result
    }

    private fun hasTrailingWhitespace(s: String): Boolean =
        s.isNotEmpty() && s.last().isWhitespace()

    private fun splitWithWhitespace(input: String): List<String> {
        if (input.isEmpty()) return listOf("")
        val out = mutableListOf<String>()
        val re = Regex("(\\s+)")
        var i = 0
        re.findAll(input).forEach { m ->
            if (m.range.first > i) {
                out.add(input.substring(i, m.range.first))
            }
            out.add(m.value)
            i = m.range.last + 1
        }
        if (i < input.length) {
            out.add(input.substring(i))
        }
        return out
    }

    private fun isAsciiOnlyShortcut(s: String): Boolean {
        for (ch in s) {
            if (ch.code > 0x7f) return false
        }
        return true
    }

    private fun resolveClafricaKey(token: String): String? {
        if (resolveDynamicDateValue(token) != null) return token
        if (tokenMap.containsKey(token)) return token
        if (isAsciiOnlyShortcut(token)) {
            val lower = token.lowercase(Locale.ROOT)
            if (lower != token && tokenMap.containsKey(lower)) return lower
        }
        return null
    }

    private fun resolveDynamicDateValue(token: String): String? {
        if (calendarMap.isEmpty()) return null
        val normalized = token.lowercase(Locale.ROOT)
        if (normalized !in todayKeywords) return null

        val today = LocalDate.now()
        val canonical = String.format(
            Locale.ROOT,
            "%02d-%02d-%04d",
            today.dayOfMonth,
            today.monthValue,
            today.year,
        )
        return calendarMap[canonical]
    }

    private fun mappedValueForCanonicalKey(key: String): String? {
        return tokenMap[key] ?: resolveDynamicDateValue(key)
    }

    private fun applyClafricaMappingToToken(token: String): String {
        if (token.isEmpty()) return token

        resolveDynamicDateValue(token)?.let { return it }
        resolveClafricaKey(token)?.let { return mappedValueForCanonicalKey(it)!! }

        val twoNum = Regex("^([a-zA-Z]+\\*?)([1-9])([1-9])$").matchEntire(token)
        if (twoNum != null) {
            val letters = twoNum.groupValues[1]
            val num1 = twoNum.groupValues[2]
            val num2 = twoNum.groupValues[3]
            val combinedKey = "$letters$num1$num2"
            resolveClafricaKey(combinedKey)?.let { return mappedValueForCanonicalKey(it)!! }
        }

        val oneNum = Regex("^([a-zA-Z]+\\*?)([1-9])$").matchEntire(token)
        if (oneNum != null) {
            val letters = oneNum.groupValues[1]
            val num = oneNum.groupValues[2]
            val combinedKey = "$letters$num"
            resolveClafricaKey(combinedKey)?.let { return mappedValueForCanonicalKey(it)!! }
        }

        for (key in allKeysSorted) {
            if (token == key) return tokenMap[key]!!
        }

        var result = token
        var changed = true
        while (changed) {
            changed = false
            for (key in allKeysSorted) {
                if (key.length > result.length) continue
                val escaped = Pattern.quote(key)
                val probe = Pattern.compile(escaped).matcher(result)
                if (!probe.find()) continue

                val value = tokenMap[key]!!
                val newResult = probe.replaceAll(
                    java.util.regex.Matcher.quoteReplacement(value)
                )
                if (newResult != result) {
                    result = newResult
                    changed = true
                    break
                }
            }
        }
        return result
    }

    private fun getLongestTrailingPrefix(token: String): String? {
        var longestSuffix: String? = null
        val lowerToken = token.lowercase(Locale.ROOT)
        for (index in token.indices) {
            val suffix = token.substring(index)
            val suffixLower = lowerToken.substring(index)
            val asciiSuffix = isAsciiOnlyShortcut(suffix)
            val matches = allKeysSorted.any { key ->
                when {
                    key.startsWith(suffix) -> true
                    asciiSuffix && isAsciiOnlyShortcut(key) && key.lowercase(Locale.ROOT).startsWith(suffixLower) -> true
                    else -> false
                }
            }
            if (matches) {
                if (longestSuffix == null || suffix.length > longestSuffix.length) {
                    longestSuffix = suffix
                }
            }
        }
        return longestSuffix
    }

    private fun getLongestTrailingExactKey(token: String): String? {
        var longestSuffix: String? = null
        for (index in token.indices) {
            val suffix = token.substring(index)
            if (resolveClafricaKey(suffix) != null) {
                if (longestSuffix == null || suffix.length > longestSuffix.length) {
                    longestSuffix = suffix
                }
            }
        }
        return longestSuffix
    }

    private fun getAmbiguousTrailingSuffix(token: String): String? {
        var longestSuffix: String? = null
        for (index in token.indices) {
            val suffix = token.substring(index)
            val canonical = resolveClafricaKey(suffix)
            if (canonical != null && ambiguousKeys.contains(canonical)) {
                if (longestSuffix == null || suffix.length > longestSuffix.length) {
                    longestSuffix = suffix
                }
            }
        }
        return longestSuffix
    }

    private fun applyLiveClafricaMappingToTrailingToken(token: String): String {
        if (token.isEmpty()) return token

        val exactTrailingKey = getLongestTrailingExactKey(token)
        val exactCanonical = exactTrailingKey?.let { resolveClafricaKey(it) }
        if (exactTrailingKey != null && exactCanonical != null && !ambiguousKeys.contains(exactCanonical)) {
            val prefix = token.substring(0, token.length - exactTrailingKey.length)
            return applyClafricaMappingToToken(prefix) + mappedValueForCanonicalKey(exactCanonical)!!
        }

        val ambiguousSuffix = getAmbiguousTrailingSuffix(token)
        if (ambiguousSuffix != null) {
            val prefix = token.substring(0, token.length - ambiguousSuffix.length)
            return applyClafricaMappingToToken(prefix) + ambiguousSuffix
        }

        val prefixSuffix = getLongestTrailingPrefix(token)
        if (prefixSuffix != null) {
            val prefix = token.substring(0, token.length - prefixSuffix.length)
            return applyClafricaMappingToToken(prefix) + prefixSuffix
        }

        return applyClafricaMappingToToken(token)
    }

    private fun finalizeClafricaToken(token: String): String {
        if (token.isEmpty()) return token
        var current = token
        var changed = true
        while (changed) {
            changed = false
            val exactTrailingKey = getLongestTrailingExactKey(current)
            val exactCanonical = exactTrailingKey?.let { resolveClafricaKey(it) }
            if (exactTrailingKey != null && exactCanonical != null) {
                val prefix = current.substring(0, current.length - exactTrailingKey.length)
                val next = applyClafricaMappingToToken(prefix) + mappedValueForCanonicalKey(exactCanonical)!!
                if (next != current) {
                    current = next
                    changed = true
                    continue
                }
            }
            val fullyMapped = applyClafricaMappingToToken(current)
            if (fullyMapped != current) {
                current = fullyMapped
                changed = true
            }
        }
        return current
    }
}
