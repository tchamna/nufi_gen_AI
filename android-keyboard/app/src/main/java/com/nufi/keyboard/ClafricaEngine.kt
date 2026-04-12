package com.nufi.keyboard

import android.content.Context
import org.json.JSONObject
import java.util.Locale
import java.util.regex.Pattern

/**
 * Mirrors [clafricaMapping.ts]: applies Clafrica shortcuts in the IME using [assets/clafrica.json].
 */
class ClafricaEngine(context: Context) {

    private val map: Map<String, String>
    private val allKeysSorted: List<String>
    private val ambiguousKeys: Set<String>

    init {
        val jsonText = context.assets.open("clafrica.json").bufferedReader(Charsets.UTF_8).use { it.readText() }
        val json = JSONObject(jsonText)
        val m = LinkedHashMap<String, String>()
        val it = json.keys()
        while (it.hasNext()) {
            val k = it.next()
            m[k] = json.getString(k)
        }
        map = m
        allKeysSorted = map.keys.sortedWith(compareBy<String> { -it.length }.thenBy { it })
        ambiguousKeys = allKeysSorted.filter { key ->
            allKeysSorted.any { other -> other.length > key.length && other.startsWith(key) }
        }.toSet()
    }

    fun applyClafricaMapping(input: String, preserveAmbiguousTrailingToken: Boolean): String {
        if (input.isEmpty()) return input
        val segments = splitWithWhitespace(input)
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
        return splitWithWhitespace(input).joinToString("") { segment ->
            if (segment.matches(Regex("\\s+"))) segment else finalizeClafricaToken(segment)
        }
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
        if (map.containsKey(token)) return token
        if (isAsciiOnlyShortcut(token)) {
            val lower = token.lowercase(Locale.ROOT)
            if (lower != token && map.containsKey(lower)) return lower
        }
        return null
    }

    private fun escapeRegex(s: String): String =
        s.replace(Regex("[.*+?^${'$'}{}()|\\[\\]\\\\\\\\]"), "\\\\$0")

    private fun applyClafricaMappingToToken(token: String): String {
        if (token.isEmpty()) return token

        resolveClafricaKey(token)?.let { return map[it]!! }

        val twoNum = Regex("^([a-zA-Z]+\\*?)([1-9])([1-9])$").matchEntire(token)
        if (twoNum != null) {
            val letters = twoNum.groupValues[1]
            val num1 = twoNum.groupValues[2]
            val num2 = twoNum.groupValues[3]
            val combinedKey = "$letters$num1$num2"
            resolveClafricaKey(combinedKey)?.let { return map[it]!! }
        }

        val oneNum = Regex("^([a-zA-Z]+\\*?)([1-9])$").matchEntire(token)
        if (oneNum != null) {
            val letters = oneNum.groupValues[1]
            val num = oneNum.groupValues[2]
            val combinedKey = "$letters$num"
            resolveClafricaKey(combinedKey)?.let { return map[it]!! }
        }

        for (key in allKeysSorted) {
            if (token == key) return map[key]!!
        }

        var result = token
        var changed = true
        while (changed) {
            changed = false
            for (key in allKeysSorted) {
                if (key.length > result.length) continue
                val escaped = escapeRegex(key)
                val insens = isAsciiOnlyShortcut(key)
                val probe = if (insens) {
                    Pattern.compile(escaped, Pattern.CASE_INSENSITIVE or Pattern.UNICODE_CASE).matcher(result)
                } else {
                    Pattern.compile(escaped).matcher(result)
                }
                if (!probe.find()) continue

                val value = map[key]!!
                val flags = if (insens) Pattern.CASE_INSENSITIVE or Pattern.UNICODE_CASE else 0
                val newResult = Pattern.compile(escaped, flags).matcher(result).replaceAll(
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
            return applyClafricaMappingToToken(prefix) + map[exactCanonical]!!
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
                val next = applyClafricaMappingToToken(prefix) + map[exactCanonical]!!
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
