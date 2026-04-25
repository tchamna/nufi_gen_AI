# Nufi Windows Keyboard

This is a Windows desktop typing agent inspired by the `input-method` repo and wired to the same Nufi transform and prediction flow as the Android keyboard.

What it does:

- runs globally across Windows text fields
- transforms Nufi shortcuts as you type
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

Customizable desktop version:

```powershell
py windows_desktop\run_nufi_windows_keyboard_customizable.py
```

Stable fallback version:

```powershell
py windows_desktop\run_nufi_windows_keyboard_stable.py
```

Use another API base URL:

```powershell
py windows_desktop\run_nufi_windows_keyboard.py --api-base-url http://127.0.0.1:8010
```

## Notes

- The packaged app runs as a standard user and does not request UAC elevation.
- It works in normal user-level apps without corporate admin rights.
- Windows will still block keyboard hook interaction with apps that are themselves running elevated.
- The desktop UI now starts in French and includes a clickable `English` switch in the app window.
- The suggestion overlay is restored against the last active typing window before it injects a selected suggestion.
- The transform engine loads the same assets used by Android:
  - `android-keyboard/app/src/main/assets/clafrica.json`
  - `android-keyboard/app/src/main/assets/nufi_sms.json`
  - `android-keyboard/app/src/main/assets/nufi_calendar.json`
- The customizable build stores user shortcuts in `%APPDATA%\Clafrica Plus Customizable\custom_shortcuts.tsv`.
- In the customizable build, press `Ctrl+Alt+S` or click `Shortcuts` to edit and reload custom mappings after install.

## Custom shortcuts

The customizable build keeps two shortcut layers:

- Built-in shortcuts from the packaged app are always loaded.
- Your custom shortcuts are added on top of that built-in list.
- If your custom file uses a shortcut that already exists in the built-in list, your custom value overrides the built-in one.
- If your custom file adds a brand-new shortcut, it is appended as an extra shortcut.
- If your custom file contains `!shortcut`, that shortcut is removed from the active shortcut set.

The custom shortcut file lives here:

```text
%APPDATA%\Clafrica Plus Customizable\custom_shortcuts.tsv
```

### Enter shortcuts directly in the interface

1. Launch `Clafrica Plus Customizable`.
2. Press `Ctrl+Alt+S` or click `Shortcuts`.
3. Type one shortcut per line using this format:

```text
shortcut<TAB>replacement
```

To remove a shortcut instead of replacing it:

```text
!shortcut
```

Examples:

```text
mba	mbe'
af 	ɑ
!mbk
```

4. Click `Save And Reload`.

Notes:

- Lines starting with `#` are ignored.
- Phrase shortcuts with spaces are allowed.
- The editor saves only your custom list, not the built-in list.

### Import from CSV, TSV, or text

The `Import File` button accepts `.csv`, `.tsv`, and `.txt`.

Supported file shapes:

- CSV/TSV with two columns such as `shortcut,replacement`
- CSV/TSV with a header row such as `shortcut,replacement`
- Text files using `shortcut<TAB>replacement`
- Text files using `shortcut=replacement`, `shortcut->replacement`, `shortcut=>replacement`, `shortcut;replacement`, or `shortcut,replacement`
- Removal rows using `!shortcut`

Import behavior:

- Imported shortcuts are merged into your current custom editor list.
- If an imported shortcut already exists in your custom editor list, the imported value replaces that custom value.
- If an imported row is `!shortcut`, that shortcut is marked for removal.
- Built-in packaged shortcuts are not deleted by import.
- Click `Save And Reload` after import to apply the merged result.

## Build an exe

```powershell
cd windows_desktop
.\build_exe.bat
```
