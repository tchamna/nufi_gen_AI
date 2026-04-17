package com.nufi.keyboard

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.inputmethodservice.Keyboard
import android.inputmethodservice.KeyboardView
import android.util.AttributeSet
import kotlin.math.max

class NufiKeyboardView(context: Context, attrs: AttributeSet) : KeyboardView(context, attrs) {

    private val density = resources.displayMetrics.density
    private val scaledDensity = resources.displayMetrics.scaledDensity

    private val paint = Paint().apply {
        textAlign = Paint.Align.CENTER
        textSize = 12f * scaledDensity
        color = Color.parseColor("#B3FFFFFF")
        typeface = Typeface.DEFAULT
        isAntiAlias = true
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val keys = keyboard?.keys ?: return
        for (key in keys) {
            val popupChars = key.popupCharacters
            val popupRes = key.popupResId
            
            var hint: String? = null
            
            // 1. Try to find a symbol hint in popupCharacters
            if (popupChars != null && popupChars.isNotEmpty()) {
                hint = findHint(popupChars.toString())
            }
            
            // 2. If not found, try getting it from XML resource
            if (hint == null && popupRes != 0) {
                hint = getSymbolHintFromResId(popupRes)
            }

            if (hint != null && key.label != null) {
                drawHint(canvas, key, hint)
            }
        }
    }

    private fun getSymbolHintFromResId(resId: Int): String? {
        return when (resId) {
            R.xml.popup_0 -> ")"
            R.xml.popup_1 -> "+"
            R.xml.popup_2 -> "="
            R.xml.popup_3 -> "*"
            R.xml.popup_4 -> "-"
            R.xml.popup_5 -> "/"
            R.xml.popup_6 -> "%"
            R.xml.popup_7 -> "&"
            R.xml.popup_8 -> "#"
            R.xml.popup_9 -> "("
            R.xml.popup_a -> "@"
            R.xml.popup_b -> "ɓ"
            R.xml.popup_c -> "ç"
            R.xml.popup_d -> "ɗ"
            R.xml.popup_e -> "ə"
            R.xml.popup_f -> "?"
            R.xml.popup_g -> "'"
            R.xml.popup_h -> "{"
            R.xml.popup_i -> "ɨ"
            R.xml.popup_j -> "}"
            R.xml.popup_k -> "<"
            R.xml.popup_l -> ">"
            R.xml.popup_n -> "*"
            R.xml.popup_o -> "ɔ"
            R.xml.popup_period -> "?"
            R.xml.popup_m -> "!"
            R.xml.popup_s -> "_"
            R.xml.popup_u -> "ʉ"
            R.xml.popup_v -> "'"
            R.xml.popup_x -> ";"
            R.xml.popup_z -> ":"
            else -> null
        }
    }

    private fun findHint(popupCharacters: String): String? {
        // List of symbols we want to prioritize as hints
        val specialHints = listOf("*", "'", "-", "!", "@", "#", "$", "%", "&", "(", ")", "+", "=", ":", ";", ",", "?", "[", "]", "{", "}", "<", ">", "|", "\\")
        
        for (s in specialHints) {
            if (popupCharacters.contains(s)) return s
        }
        
        // If it's a single character popup (like numbers on q,w,e...), show it
        if (popupCharacters.length == 1) {
            return popupCharacters
        }
        
        return null
    }

    private fun drawHint(canvas: Canvas, key: Keyboard.Key, hint: String) {
        val x = key.x + key.width - (9f * density)
        val y = key.y + max(14f * density, paint.textSize)
        canvas.drawText(hint, x, y, paint)
    }
}
