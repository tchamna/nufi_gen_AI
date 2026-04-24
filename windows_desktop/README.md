# Nufi Windows Keyboard

This is a Windows desktop typing agent inspired by the `input-method` repo and wired to the same Nufi transform and prediction flow as the Android keyboard.

What it does:

- runs globally across Windows text fields
- finalizes Nufi keyboard transforms when you press `Space`, `Tab`, `Enter`, or punctuation delimiters
- calls the same prediction API route as Android: `/api/keyboard/suggest`
- shows a small always-on-top suggestion strip
- inserts suggestions with `Ctrl+Shift+1` through `Ctrl+Shift+5`
- toggles the agent on or off with double `Shift`
- quits with `Ctrl+Alt+Q`

What it is not:

- not a native Windows TSF IME yet
- not a caret-anchored suggestion popup
- not full Android-style per-keystroke composition inside every app

That tradeoff is deliberate. This gets a working Windows-wide keyboard agent quickly. A true Windows IME is the next step if you want exact native composition behavior inside Word, Excel, Chrome, and Google Docs.

## Run locally

From the repo root:

```powershell
py -m pip install -r windows_desktop\requirements.txt
py windows_desktop\run_nufi_windows_keyboard.py
```

Use another API base URL:

```powershell
py windows_desktop\run_nufi_windows_keyboard.py --api-base-url http://127.0.0.1:8010
```

## Notes

- The packaged app runs as a standard user and does not request UAC elevation.
- It works in normal user-level apps without corporate admin rights.
- Windows will still block keyboard hook interaction with apps that are themselves running elevated.
- The suggestion overlay is restored against the last active typing window before it injects a selected suggestion.
- The transform engine loads the same assets used by Android:
  - `android-keyboard/app/src/main/assets/clafrica.json`
  - `android-keyboard/app/src/main/assets/nufi_sms.json`
  - `android-keyboard/app/src/main/assets/nufi_calendar.json`

## Build an exe

```powershell
cd windows_desktop
.\build_exe.bat
```
