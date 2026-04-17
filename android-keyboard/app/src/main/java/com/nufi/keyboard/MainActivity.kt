package com.nufi.keyboard

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.inputmethod.InputMethodManager
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.button.MaterialButtonToggleGroup

class MainActivity : AppCompatActivity() {
    private lateinit var settings: KeyboardSettings

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        settings = KeyboardSettings(this)

        val openSettingsButton = findViewById<MaterialButton>(R.id.openKeyboardSettingsButton)
        val chooseKeyboardButton = findViewById<MaterialButton>(R.id.chooseKeyboardButton)
        val layoutToggleGroup = findViewById<MaterialButtonToggleGroup>(R.id.layoutToggleGroup)

        when (settings.getLayoutType()) {
            KeyboardSettings.LAYOUT_AZERTY -> layoutToggleGroup.check(R.id.layoutAzerty)
            else -> layoutToggleGroup.check(R.id.layoutQwerty)
        }
        layoutToggleGroup.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (!isChecked) return@addOnButtonCheckedListener
            when (checkedId) {
                R.id.layoutAzerty -> settings.setLayoutType(KeyboardSettings.LAYOUT_AZERTY)
                R.id.layoutQwerty -> settings.setLayoutType(KeyboardSettings.LAYOUT_QWERTY)
            }
        }

        openSettingsButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        }

        chooseKeyboardButton.setOnClickListener {
            val imm = getSystemService(InputMethodManager::class.java)
            imm?.showInputMethodPicker()
        }
    }
}
