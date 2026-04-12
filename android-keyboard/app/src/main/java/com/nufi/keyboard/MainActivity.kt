package com.nufi.keyboard

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.inputmethod.InputMethodManager
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText

class MainActivity : AppCompatActivity() {
    private lateinit var settings: KeyboardSettings

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        settings = KeyboardSettings(this)

        val baseUrlField = findViewById<TextInputEditText>(R.id.baseUrlField)
        val saveButton = findViewById<MaterialButton>(R.id.saveButton)
        val openSettingsButton = findViewById<MaterialButton>(R.id.openKeyboardSettingsButton)
        val chooseKeyboardButton = findViewById<MaterialButton>(R.id.chooseKeyboardButton)

        baseUrlField.setText(settings.getBaseUrl())

        saveButton.setOnClickListener {
            val value = baseUrlField.text?.toString().orEmpty()
            if (value.isBlank()) {
                Toast.makeText(this, R.string.base_url_required, Toast.LENGTH_SHORT).show()
            } else {
                settings.setBaseUrl(value)
                Toast.makeText(this, R.string.settings_saved, Toast.LENGTH_SHORT).show()
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
