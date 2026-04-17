# Android Keyboard Client

This folder contains a minimal Android IME client for the Nufi suggestion API.

## What it does

- shows a QWERTY keyboard (letters + number row)
- applies **Clafrica** shortcuts (same rules as `clafricaMapping.ts`) from bundled `assets/clafrica.json` after each key
- fetches next-word suggestions from `POST /api/keyboard/suggest`
- lets the user tap a suggestion to insert it into the current field
- stores the API base URL in shared preferences

## Expected API URL

**Default (production):** the Azure App Service URL (HTTPS), e.g.

`https://nufi-gen-ai-dug3ggdsh3fze9e5.canadacentral-01.azurewebsites.net`

Set in **KeyboardSettings** / launcher screen; no trailing slash. The keyboard calls `POST {base}/api/keyboard/suggest`.

**Local API:** use `http://10.0.2.2:8010` on the Android emulator, or `http://<your-PC-LAN-IP>:8010` on a physical device, and save it in the launcher app.

## Run order

1. Start the Python API from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_app.ps1
```

2. Open `android-keyboard` in Android Studio.
3. Let Gradle sync.
4. Install the app on an emulator or device.
5. Open the app and save the correct API URL.
6. Enable `Nufi Keyboard` in Android keyboard settings.
7. Switch the active keyboard to `Nufi Keyboard`.

## Updating the Clafrica map

The Android keyboard uses two shortcut assets:

- `app/src/main/assets/clafrica.json` for the base **Clafrica** shortcuts from `../clafricaMapping.ts`
- `app/src/main/assets/nufi_sms.json` for the extra SMS shortcuts from `nufi_sms_and_calendar.xlsx`, sheet `Nufi_SMS`
- `app/src/main/assets/nufi_calendar.json` for the calendar date expansions from `nufi_sms_and_calendar.xlsx`, sheet `Nufi_Calendar`

The keyboard also resolves these runtime aliases in the same calendar format:
`today*`, `aujourd'hui*`, `aujourdhui*`, `date*`, `l'nz`, `ze'e*`, `now*`, `yesterday*`, `*waha`, `tomorrow*`, `waha*`

To regenerate the JSON asset:

```powershell
python .\tools\generate_clafrica_from_sms.py
```

Then rebuild the APK.

## Notes

- This is a first IME scaffold, not a finished production keyboard.
- The keyboard layout is intentionally small and simple.
- Suggestions currently use `n = 4` and a limit of 5 in the IME service.
