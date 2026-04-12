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
        var shouldClafrica = false
        when (primaryCode) {
            Keyboard.KEYCODE_DELETE -> {
                inputConnection.deleteSurroundingText(1, 0)
                shouldClafrica = true
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
                val character = when {
                    primaryCode <= 0 -> return
                    shiftEnabled -> primaryCode.toChar().uppercaseChar()
                    else -> primaryCode.toChar()
                }
                inputConnection.commitText(character.toString(), 1)
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

    override fun onPress(primaryCode: Int) = Unit
    override fun onRelease(primaryCode: Int) = Unit
    override fun onText(text: CharSequence?) = Unit
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
