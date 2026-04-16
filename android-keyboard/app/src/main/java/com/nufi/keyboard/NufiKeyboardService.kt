package com.nufi.keyboard

import android.inputmethodservice.InputMethodService
import android.inputmethodservice.Keyboard
import android.inputmethodservice.KeyboardView
import android.os.Handler
import android.os.Looper
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class NufiKeyboardService : InputMethodService(), KeyboardView.OnKeyboardActionListener {
    private lateinit var keyboardView: NufiKeyboardView
    private lateinit var suggestionStrip: LinearLayout
    private lateinit var statusView: TextView
    private lateinit var qwertyKeyboard: Keyboard
    private lateinit var symbolsKeyboard: Keyboard
    private var isSymbols = false
    private lateinit var apiClient: KeyboardApiClient
    private lateinit var settings: KeyboardSettings
    private var clafricaEngine: ClafricaEngine? = null

    private val serviceScope = CoroutineScope(Dispatchers.Main)
    private val mainHandler = Handler(Looper.getMainLooper())
    private var shiftEnabled = false
    private var suggestJob: Job? = null
    private var isLongPress = false
    private var shouldClafrica = false

    private val customCodes = mapOf(
        2001 to "\u0251\u0300",
        2002 to "\u0251\u0301",
        2003 to "\u0251\u0304",
        2004 to "\u0251\u030c",
        2005 to "\u0251\u0302",
        2006 to "\u025b\u0300",
        2007 to "\u025b\u0301",
        2008 to "\u025b\u0304",
        2009 to "\u025b\u030c",
        2010 to "\u025b\u0302",
        2011 to "\u0259\u0300",
        2012 to "\u0259\u0301",
        2013 to "\u0259\u0304",
        2014 to "\u0259\u030c",
        2015 to "\u0259\u0302",
        2016 to "\u0268\u0300",
        2017 to "\u0268\u0301",
        2018 to "\u0268\u0304",
        2019 to "\u0268\u030c",
        2020 to "\u0268\u0302",
        2021 to "\u0254\u0300",
        2022 to "\u0254\u0301",
        2023 to "\u0254\u0304",
        2024 to "\u0254\u030c",
        2025 to "\u0254\u0302",
        2026 to "\u0289\u0300",
        2027 to "\u0289\u0301",
        2028 to "\u0289\u0304",
        2029 to "\u0289\u030c",
        2030 to "\u0289\u0302",
    )

    private val longPressRunnable = object : Runnable {
        override fun run() {
            isLongPress = true
            val ic = currentInputConnection
            if (ic != null) {
                ic.beginBatchEdit()
                val before = ic.getTextBeforeCursor(100, 0)
                if (before != null && before.isNotEmpty()) {
                    val lastWordMatch = Regex("(\\w+|\\s+|[^\\w\\s]+)$").find(before)
                    val lengthToDelete = lastWordMatch?.value?.length ?: 1
                    ic.deleteSurroundingText(lengthToDelete, 0)
                }
                ic.endBatchEdit()
                mainHandler.postDelayed(this, 300)
            }
        }
    }

    private val suggestRunnable = Runnable {
        if (::suggestionStrip.isInitialized && ::statusView.isInitialized) {
            fetchSuggestions()
        }
    }

    private val clafricaApplyRunnable = Runnable {
        if (::suggestionStrip.isInitialized) {
            currentInputConnection?.let { applyClafricaToTextBeforeCursorNow(it) }
        }
    }

    override fun onCreate() {
        super.onCreate()
        apiClient = KeyboardApiClient()
        settings = KeyboardSettings(this)
        clafricaEngine = ClafricaEngine(this)
    }

    override fun onCreateInputView(): View {
        val root = layoutInflater.inflate(R.layout.input_view, null)
        suggestionStrip = root.findViewById(R.id.suggestionStrip)
        statusView = root.findViewById(R.id.statusView)
        keyboardView = root.findViewById(R.id.keyboardView)
        qwertyKeyboard = Keyboard(this, R.xml.qwerty)
        symbolsKeyboard = Keyboard(this, R.xml.symbols)

        keyboardView.setPopupParent(root)
        keyboardView.isPreviewEnabled = false
        keyboardView.setOnKeyboardActionListener(this)
        setKeyboardLayout(false)

        renderSuggestions(emptyList())
        return root
    }

    override fun onEvaluateInputViewShown(): Boolean {
        super.onEvaluateInputViewShown()
        return true
    }

    override fun onEvaluateFullscreenMode(): Boolean = false

    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
        isSymbols = false
        shiftEnabled = false
        if (::keyboardView.isInitialized) {
            setKeyboardLayout(false)
        }
        refreshSuggestions()
    }

    override fun onStartInputView(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(attribute, restarting)
        if (::keyboardView.isInitialized) {
            setKeyboardLayout(isSymbols)
        }
    }

    override fun onDestroy() {
        mainHandler.removeCallbacks(clafricaApplyRunnable)
        mainHandler.removeCallbacks(suggestRunnable)
        serviceScope.cancel()
        super.onDestroy()
    }

    override fun onKey(primaryCode: Int, keyCodes: IntArray?) {
        if (!::keyboardView.isInitialized) return
        val inputConnection = currentInputConnection ?: return
        shouldClafrica = false
        when (primaryCode) {
            Keyboard.KEYCODE_DELETE -> {
                if (!isLongPress) {
                    inputConnection.deleteSurroundingText(1, 0)
                    shouldClafrica = true
                }
            }
            Keyboard.KEYCODE_SHIFT -> {
                shiftEnabled = !shiftEnabled
                keyboardView.isShifted = shiftEnabled
                keyboardView.invalidateAllKeys()
            }
            Keyboard.KEYCODE_DONE -> sendEnterOrEditorAction(inputConnection)
            Keyboard.KEYCODE_MODE_CHANGE -> setKeyboardLayout(!isSymbols)
            32 -> {
                inputConnection.commitText(" ", 1)
                shouldClafrica = true
            }
            else -> {
                val customString = customCodes[primaryCode]
                if (customString != null) {
                    val text = if (shiftEnabled) {
                        customString.map { ch ->
                            when (ch) {
                                '\u0251' -> '\u2c6d'
                                '\u025b' -> '\u0190'
                                '\u0259' -> '\u018f'
                                '\u0268' -> '\u0197'
                                '\u0254' -> '\u0186'
                                '\u0289' -> '\u0244'
                                else -> ch.uppercaseChar()
                            }
                        }.joinToString("")
                    } else {
                        customString
                    }
                    inputConnection.commitText(text, 1)
                } else {
                    val character = when {
                        primaryCode <= 0 -> return
                        shiftEnabled -> primaryCode.toChar().uppercaseChar()
                        else -> primaryCode.toChar()
                    }
                    inputConnection.commitText(character.toString(), 1)
                }
                if (shiftEnabled) {
                    shiftEnabled = false
                    keyboardView.isShifted = false
                    keyboardView.invalidateAllKeys()
                }
                shouldClafrica = true
            }
        }
        if (shouldClafrica) {
            scheduleClafricaApply()
        }
        refreshSuggestions()
    }

    private fun scheduleClafricaApply() {
        mainHandler.removeCallbacks(clafricaApplyRunnable)
        mainHandler.postDelayed(clafricaApplyRunnable, CLAFRICA_APPLY_DELAY_MS)
    }

    private fun applyClafricaToTextBeforeCursorNow(ic: InputConnection) {
        val engine = clafricaEngine ?: return
        val before = ic.getTextBeforeCursor(CLAFRICA_BEFORE_CURSOR_MAX, 0)?.toString() ?: return
        val mapped = engine.applyClafricaMapping(before, preserveAmbiguousTrailingToken = true)
        if (mapped == before) return
        ic.beginBatchEdit()
        try {
            ic.deleteSurroundingText(before.length, 0)
            ic.commitText(mapped, 1)
        } finally {
            ic.endBatchEdit()
        }
    }

    override fun onPress(primaryCode: Int) {
        if (primaryCode == Keyboard.KEYCODE_DELETE) {
            isLongPress = false
            mainHandler.postDelayed(longPressRunnable, 500)
        }
    }

    override fun onRelease(primaryCode: Int) {
        if (primaryCode == Keyboard.KEYCODE_DELETE) {
            mainHandler.removeCallbacks(longPressRunnable)
        }
    }

    override fun onText(text: CharSequence?) {
        val inputConnection = currentInputConnection ?: return
        if (text == null) return
        inputConnection.commitText(text, 1)
        scheduleClafricaApply()
    }

    override fun swipeLeft() = Unit
    override fun swipeRight() = Unit
    override fun swipeDown() = Unit
    override fun swipeUp() = Unit

    private fun sendEnterOrEditorAction(ic: InputConnection) {
        ic.finishComposingText()
        val info = currentInputEditorInfo ?: return

        val packageName = info.packageName.orEmpty()
        val actionId = info.imeOptions and EditorInfo.IME_MASK_ACTION
        val isMultiLine = (info.inputType and EditorInfo.TYPE_TEXT_FLAG_MULTI_LINE) != 0

        val actionCandidates = mutableListOf<Int>()
        if (isLikelyMessagingEditor(packageName)) {
            actionCandidates += EditorInfo.IME_ACTION_SEND
        }
        if (actionId != EditorInfo.IME_ACTION_NONE && actionId != EditorInfo.IME_ACTION_UNSPECIFIED && actionId != EditorInfo.IME_ACTION_DONE) {
            actionCandidates += actionId
        }
        if (EditorInfo.IME_ACTION_SEND !in actionCandidates) {
            actionCandidates += EditorInfo.IME_ACTION_SEND
        }
        if (!isMultiLine && actionId == EditorInfo.IME_ACTION_DONE) {
            actionCandidates += EditorInfo.IME_ACTION_DONE
        }

        for (candidate in actionCandidates.distinct()) {
            if (ic.performEditorAction(candidate)) {
                return
            }
        }

        if (isMultiLine) {
            ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
            ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
            return
        }

        ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
        ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
    }

    private fun isLikelyMessagingEditor(packageName: String): Boolean {
        return packageName.contains("whatsapp", ignoreCase = true) ||
            packageName.contains("telegram", ignoreCase = true) ||
            packageName.contains("signal", ignoreCase = true) ||
            packageName.contains("messaging", ignoreCase = true) ||
            packageName.contains("messenger", ignoreCase = true)
    }

    private fun refreshSuggestions() {
        mainHandler.removeCallbacks(suggestRunnable)
        mainHandler.postDelayed(suggestRunnable, 200)
    }

    private fun setKeyboardLayout(showSymbols: Boolean) {
        isSymbols = showSymbols
        shiftEnabled = false
        keyboardView.keyboard = if (showSymbols) symbolsKeyboard else qwertyKeyboard
        keyboardView.isShifted = false
        updateActionKeyLabels()
        keyboardView.invalidateAllKeys()
    }

    private fun updateActionKeyLabels() {
        val actionLabel = resolveActionKeyLabel()
        applyActionKeyLabel(qwertyKeyboard, actionLabel)
        applyActionKeyLabel(symbolsKeyboard, actionLabel)
    }

    private fun resolveActionKeyLabel(): CharSequence {
        val info = currentInputEditorInfo
        val actionId = info?.imeOptions?.and(EditorInfo.IME_MASK_ACTION) ?: EditorInfo.IME_ACTION_UNSPECIFIED
        val isMultiLine = info != null && (info.inputType and EditorInfo.TYPE_TEXT_FLAG_MULTI_LINE) != 0
        return when {
            isMultiLine -> "Enter"
            actionId == EditorInfo.IME_ACTION_GO -> "Go"
            actionId == EditorInfo.IME_ACTION_NEXT -> "Next"
            actionId == EditorInfo.IME_ACTION_SEARCH -> "Search"
            actionId == EditorInfo.IME_ACTION_SEND -> "Send"
            actionId == EditorInfo.IME_ACTION_DONE -> "Done"
            else -> "Enter"
        }
    }

    private fun applyActionKeyLabel(keyboard: Keyboard, label: CharSequence) {
        keyboard.keys
            .firstOrNull { it.codes?.firstOrNull() == Keyboard.KEYCODE_DONE }
            ?.let { key ->
                key.label = label
                key.text = null
            }
    }

    private fun fetchSuggestions() {
        if (!::suggestionStrip.isInitialized || !::statusView.isInitialized) return
        suggestJob?.cancel()
        val beforeCursor = currentInputConnection?.getTextBeforeCursor(80, 0)?.toString().orEmpty()
        if (beforeCursor.isBlank()) {
            renderSuggestions(emptyList())
            return
        }

        statusView.text = getString(R.string.fetching_suggestions)
        suggestJob = serviceScope.launch {
            val result = apiClient.fetchSuggestions(
                baseUrl = settings.getBaseUrl(),
                text = beforeCursor,
                n = 4,
                limit = 5,
            )

            if (!::suggestionStrip.isInitialized || !::statusView.isInitialized) return@launch

            if (result.isSuccess) {
                val payload = result.getOrThrow()
                statusView.text = getString(R.string.suggestion_context_template, payload.usedContext)
                renderSuggestions(payload.suggestions)
            } else {
                statusView.text = getString(R.string.suggestion_error)
                renderSuggestions(emptyList())
            }
        }
    }

    private fun renderSuggestions(suggestions: List<KeyboardSuggestion>) {
        if (!::suggestionStrip.isInitialized) return
        suggestionStrip.removeAllViews()

        if (suggestions.isEmpty()) {
            val emptyView = TextView(this).apply {
                text = getString(R.string.no_suggestions)
                textSize = 14f
                setPadding(32, 0, 32, 0)
            }
            suggestionStrip.addView(emptyView)
            return
        }

        suggestions.forEach { suggestion ->
            val button = layoutInflater.inflate(R.layout.suggestion_button, suggestionStrip, false) as Button
            button.text = suggestion.word
            button.setOnClickListener {
                val ic = currentInputConnection ?: return@setOnClickListener
                val before = ic.getTextBeforeCursor(1, 0)
                val spacePrefix = if (before.isNullOrEmpty() || before.last().isWhitespace()) "" else " "
                ic.commitText("$spacePrefix${suggestion.word} ", 1)
                applyClafricaToTextBeforeCursorNow(ic)
                refreshSuggestions()
            }
            suggestionStrip.addView(button)
        }
    }

    companion object {
        private const val CLAFRICA_BEFORE_CURSOR_MAX = 4000
        private const val CLAFRICA_APPLY_DELAY_MS = 45L
    }
}
