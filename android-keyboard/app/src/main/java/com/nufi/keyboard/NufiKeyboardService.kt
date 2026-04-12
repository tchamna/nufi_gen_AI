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
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class NufiKeyboardService : InputMethodService(), KeyboardView.OnKeyboardActionListener {
    private lateinit var keyboardView: KeyboardView
    private lateinit var suggestionStrip: LinearLayout
    private lateinit var statusView: TextView
    private lateinit var qwertyKeyboard: Keyboard
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
        2001 to "ɑ̀", 2002 to "ɑ́", 2003 to "ɑ̄", 2004 to "ɑ̌", 2005 to "ɑ̂",
        2006 to "ɛ̀", 2007 to "ɛ́", 2008 to "ɛ̄", 2009 to "ɛ̌", 2010 to "ɛ̂",
        2011 to "ə̀", 2012 to "ə́", 2013 to "ə̄", 2014 to "ə̌", 2015 to "ə̂",
        2016 to "ɨ̀", 2017 to "ɨ́", 2018 to "ɨ̄", 2019 to "ɨ̌", 2020 to "ɨ̂",
        2021 to "ɔ̀", 2022 to "ɔ́", 2023 to "ɔ̄", 2024 to "ɔ̌", 2025 to "ɔ̂",
        2026 to "ʉ̀", 2027 to "ʉ́", 2028 to "ʉ̄", 2029 to "ʉ̌", 2030 to "ʉ̂"
    )

    private val longPressRunnable = Runnable {
        isLongPress = true
        val ic = currentInputConnection
        if (ic != null) {
            ic.beginBatchEdit()
            val before = ic.getTextBeforeCursor(10000, 0)
            val after = ic.getTextAfterCursor(10000, 0)
            ic.deleteSurroundingText(before?.length ?: 0, after?.length ?: 0)
            ic.endBatchEdit()
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

        keyboardView.keyboard = qwertyKeyboard
        keyboardView.isPreviewEnabled = false
        keyboardView.setOnKeyboardActionListener(this)

        renderSuggestions(emptyList())
        return root
    }

    override fun onEvaluateInputViewShown(): Boolean = true

    override fun onEvaluateFullscreenMode(): Boolean = false

    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
        shiftEnabled = false
        if (::keyboardView.isInitialized) {
            keyboardView.isShifted = false
            keyboardView.invalidateAllKeys()
        }
        refreshSuggestions()
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
                                'ɑ' -> 'Ɑ'
                                'ɛ' -> 'Ɛ'
                                'ə' -> 'Ə'
                                'ɨ' -> 'Ɨ'
                                'ɔ' -> 'Ɔ'
                                'ʉ' -> 'Ʉ'
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

    /**
     * Debounced: bulk replace on every key makes many apps call [InputConnection.finishComposingText] /
     * restart input and hide the IME. We apply shortly after typing pauses and batch the replace.
     */
    private fun scheduleClafricaApply() {
        mainHandler.removeCallbacks(clafricaApplyRunnable)
        mainHandler.postDelayed(clafricaApplyRunnable, CLAFRICA_APPLY_DELAY_MS)
    }

    /**
     * Runs the same Clafrica rules as the web app on text before the cursor (see [ClafricaEngine]).
     */
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
        requestShowSelf(InputMethodManager.SHOW_IMPLICIT)
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

        var output = text.toString()
        if (shiftEnabled) {
            output = output.map { ch ->
                when (ch) {
                    'ɑ' -> 'Ɑ'
                    'ɛ' -> 'Ɛ'
                    'ə' -> 'Ə'
                    'ɨ' -> 'Ɨ'
                    'ɔ' -> 'Ɔ'
                    'ʉ' -> 'Ʉ'
                    else -> ch.uppercaseChar()
                }
            }.joinToString("")
        }

        inputConnection.commitText(output, 1)

        if (shiftEnabled) {
            shiftEnabled = false
            keyboardView.isShifted = false
            keyboardView.invalidateAllKeys()
        }
        scheduleClafricaApply()
    }
    override fun swipeLeft() = Unit
    override fun swipeRight() = Unit
    override fun swipeDown() = Unit
    override fun swipeUp() = Unit

    private fun sendEnterOrEditorAction(inputConnection: InputConnection) {
        val info = currentInputEditorInfo
        val action = info?.imeOptions?.and(EditorInfo.IME_MASK_ACTION) ?: EditorInfo.IME_ACTION_UNSPECIFIED
        if (action != EditorInfo.IME_ACTION_NONE &&
            action != EditorInfo.IME_ACTION_UNSPECIFIED &&
            inputConnection.performEditorAction(action)
        ) {
            return
        }
        inputConnection.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
        inputConnection.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
    }

    private fun refreshSuggestions() {
        mainHandler.removeCallbacks(suggestRunnable)
        mainHandler.postDelayed(suggestRunnable, 200)
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
