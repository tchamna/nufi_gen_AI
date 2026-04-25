# Windows Keyboard Handoff

Date: 2026-04-24

## Scope completed

The Windows desktop keyboard was added under `windows_desktop/` and pushed to `origin/main`.

Committed revision:
- `f46fd1c` — `Add Clafrica Plus Windows keyboard`

Primary deliverable:
- Windows desktop typing agent packaged as `Clafrica Plus`

## What was implemented

- Added the Windows desktop app source under `windows_desktop/`.
- Added the transform engine shared against Android asset files:
  - `android-keyboard/app/src/main/assets/clafrica.json`
  - `android-keyboard/app/src/main/assets/nufi_sms.json`
  - `android-keyboard/app/src/main/assets/nufi_calendar.json`
- Added prediction overlay and keyboard hook runtime in `windows_desktop/nufi_windows_keyboard/app.py`.
- Added packaging config in `windows_desktop/NufiWindowsKeyboard.spec`.
- Renamed packaged app output to `Clafrica Plus`.
- Made Windows packaging explicitly standard-user:
  - `uac_admin=False`
  - `uac_uiaccess=False`
- Updated the lock file name to `ClafricaPlus.lock`.
- Added `windows_desktop/build_exe.bat` to build:
  - `dist/Clafrica Plus.exe`
  - `share/Clafrica Plus/`
  - `share/Clafrica Plus.zip`
- Added focused tests in `tests/test_windows_desktop_engine.py`.
- Updated `.gitignore` to ignore generated Windows package outputs and local machine files.

## Overlay positioning work already done

The suggestion overlay was adjusted to avoid anchoring blindly to invalid caret coordinates.

Current behavior in code:
- validates caret coordinates against the active window rect
- positions the strip slightly to the right and below the caret when usable
- falls back to a safer in-window placement when caret coordinates look invalid

Relevant file:
- `windows_desktop/nufi_windows_keyboard/app.py`

## Validation already run

Focused tests passed:

```powershell
c:/Users/tcham/Wokspace/nufi_gen_AI/.venv/Scripts/python.exe -m pytest ..\tests\test_windows_desktop_engine.py
```

Build validation passed:

```powershell
cd windows_desktop
.\build_exe.bat
```

Zip contents were verified to include:
- `Clafrica Plus.exe`
- `README.txt`

Push completed successfully to:
- `origin/main`

## Important runtime limitations

- The packaged app does not request admin rights and should launch on normal corporate machines without a UAC elevation prompt.
- Windows will still block keyboard hook interaction with elevated target apps unless the keyboard app is also elevated.
- Browser caret detection may still be imperfect in some inputs because this is not a native TSF IME.

## Known improvements still needed

High-priority follow-up work:

- Validate overlay placement in real browsers and real text fields:
  - Chrome textareas
  - browser contenteditable fields
  - Google Docs
  - Word online
- Reduce or remove debug console noise in `windows_desktop/nufi_windows_keyboard/app.py`.
  - There are verbose `print(...)` statements for key events and replacements.
- Consider switching packaged mode from console to windowed if user-facing console windows are undesirable.
- Add a more robust browser fallback when `GetGUIThreadInfo` returns unusable caret coordinates.
- Add end-to-end tests or a manual verification checklist for:
  - punctuation finalization
  - suggestion selection
  - browser overlay positioning
  - non-admin startup
- Consider rebuilding and attaching packaged artifacts in CI instead of only local builds.

Medium-priority improvements:

- Add a versioned release note for the Windows keyboard.
- Add an app icon and metadata for the packaged `.exe`.
- Consider a native Windows IME/TSF implementation if exact caret-aware composition is required across apps.

## Files that matter most

- `windows_desktop/nufi_windows_keyboard/app.py`
- `windows_desktop/nufi_windows_keyboard/engine.py`
- `windows_desktop/build_exe.bat`
- `windows_desktop/NufiWindowsKeyboard.spec`
- `tests/test_windows_desktop_engine.py`
- `.gitignore`

## Current repo state after push

These local changes were still present and were intentionally not included in the Windows keyboard commit:

- modified `data/Nufi/Nufi_language_model_2gram_test.pickle`
- modified `data/Nufi/Nufi_language_model_3gram_test.pickle`
- modified `data/Nufi/Nufi_language_model_4gram_test.pickle`
- modified `data/Nufi/Nufi_language_model_5gram_test.pickle`
- modified `data/Nufi/Nufi_language_model_6gram_test.pickle`
- modified `data/Nufi/Nufi_language_model_api.pickle`
- untracked `docs/prediction_examples.md`

Next agent should avoid staging those unless that is the explicit task.

## Fast restart commands

Run from source:

```powershell
c:/Users/tcham/Wokspace/nufi_gen_AI/.venv/Scripts/python.exe windows_desktop/run_nufi_windows_keyboard.py
```

Rebuild package:

```powershell
cd windows_desktop
.\build_exe.bat
```

Packaged outputs:

- `windows_desktop/dist/Clafrica Plus.exe`
- `windows_desktop/share/Clafrica Plus/`
- `windows_desktop/share/Clafrica Plus.zip`