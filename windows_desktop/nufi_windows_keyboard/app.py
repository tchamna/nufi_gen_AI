from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
import os
import queue
import re
import sys
import tempfile
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests

from .custom_shortcuts import (
    ShortcutFileError,
    ensure_shortcuts_file,
    get_user_shortcuts_path,
    load_import_shortcuts,
    parse_shortcuts_text,
    render_shortcuts_text,
    save_shortcuts_text,
)
from .engine import NufiTransformEngine, ShortcutHint


USER32 = ctypes.windll.user32
MAPVK_VSC_TO_VK_EX = 3
LOCK_PATH = str(Path(tempfile.gettempdir()) / "ClafricaPlus.lock")
LOG_PATH = str(Path(tempfile.gettempdir()) / "ClafricaPlus.log")
TOGGLE_WINDOW_SECONDS = 0.35
POST_INJECTION_TOGGLE_GUARD_SECONDS = 0.75
SHIFT_KEYS = {"shift", "left shift", "right shift"}
SHIFT_SCAN_CODES = {42, 54}
MODIFIER_KEYS = {
    "alt",
    "left alt",
    "right alt",
    "ctrl",
    "left ctrl",
    "right ctrl",
    "windows",
    "left windows",
    "right windows",
}
NAVIGATION_KEYS = {
    "left",
    "right",
    "up",
    "down",
    "home",
    "end",
    "page up",
    "page down",
    "insert",
    "delete",
    "esc",
}
DELIMITER_KEYS = {"space": " ", "tab": "\t", "enter": "\n"}
PUNCTUATION_DELIMITERS = {".", ",", ";", ":", "!", "?", ")", "]", "}"}

# Virtual key codes for modifier keys used to patch GetKeyboardState in non-UI threads
_MODIFIER_VK_CODES = (
    0x10, 0xA0, 0xA1,  # VK_SHIFT, VK_LSHIFT, VK_RSHIFT
    0x11, 0xA2, 0xA3,  # VK_CONTROL, VK_LCONTROL, VK_RCONTROL
    0x12, 0xA4, 0xA5,  # VK_MENU, VK_LMENU, VK_RMENU
)
_VK_CAPITAL = 0x14  # VK_CAPITAL / Caps Lock
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_MBUTTON = 0x04
POINTER_OVERLAY_OFFSET_X = -24
POINTER_OVERLAY_OFFSET_Y = 64
CARET_OVERLAY_OFFSET_X = -24
CARET_OVERLAY_OFFSET_Y = 56

UI_TEXTS = {
    "fr": {
        "exit": "Quitter",
        "shortcuts": "Raccourcis",
        "language_toggle": "English",
        "footer": "Developpe par Resulam : www.resulam.com",
        "on": "ACTIF",
        "off": "ARRET",
        "toggle_hint": "Double Maj (\u2191\u2191) active/desactive",
        "shortcut_hint_prefix": "Raccourcis : ",
        "suggestions_status": "Suggestions  1..5  |  Double Maj (\u2191\u2191) active/desactive",
        "editor_title": "{mode_label} Raccourcis",
        "editor_heading": "Modifier les raccourcis personnalises",
        "file_label": "Fichier : {path}",
        "editor_help": (
            "Saisie manuelle : une ligne par raccourci au format raccourci<TAB>remplacement. "
            "Suppression : !raccourci. Import : .csv, .tsv ou .txt. "
            "Les raccourcis personnalises s'ajoutent a la liste integree ; "
            "en cas de doublon, la valeur personnalisee prend le dessus."
        ),
        "save_reload": "Enregistrer et recharger",
        "reload_file": "Recharger le fichier",
        "import_file": "Importer un fichier",
        "open_folder": "Ouvrir le dossier",
        "close": "Fermer",
        "loaded_file": "Charge : {path}",
        "reloaded_file": "Fichier recharge : {name}",
        "save_failed": "Echec de l'enregistrement : {error}",
        "import_dialog_title": "Importer des raccourcis",
        "shortcut_files": "Fichiers de raccourcis",
        "csv_files": "Fichiers CSV",
        "tsv_files": "Fichiers TSV",
        "text_files": "Fichiers texte",
        "all_files": "Tous les fichiers",
        "imported_count": (
            "Importe : {count} raccourci(s) depuis {path}. "
            "Cliquez sur \"Enregistrer et recharger\" pour appliquer."
        ),
        "ctrl_alt_s_hint": "  |  Ctrl+Alt+S raccourcis",
        "keyboard_error": "Erreur clavier dans {source}. Voir {log_path}",
        "shortcuts_reloaded": "{mode_label} a recharge les raccourcis depuis {path}",
        "custom_not_enabled": "La modification des raccourcis personnalises n'est pas activee.",
        "saved_reloaded": "Enregistre et recharge : {path}",
        "loaded_default_shortcuts_fix": (
            "{mode_label} a charge les raccourcis par defaut. "
            "Appuyez sur Ctrl+Alt+S pour corriger : {error}"
        ),
        "app_description": "Clavier Windows Clafrica+",
        "mode_live_default": "Clafrica+",
        "mode_stable_default": "Clafrica+ Stable",
        "mode_live_custom": "Clafrica+ Personnalisable",
        "mode_stable_custom": "Clafrica+ Personnalisable Stable",
    },
    "en": {
        "exit": "Exit",
        "shortcuts": "Shortcuts",
        "language_toggle": "Francais",
        "footer": "Developed by Resulam: www.resulam.com",
        "on": "ON",
        "off": "OFF",
        "toggle_hint": "Double-Shift (\u2191\u2191) toggles ON/OFF",
        "shortcut_hint_prefix": "Shortcuts: ",
        "suggestions_status": "Suggestions  1..5  |  Double-Shift (\u2191\u2191) toggles ON/OFF",
        "editor_title": "{mode_label} Shortcuts",
        "editor_heading": "Edit custom shortcuts",
        "file_label": "File: {path}",
        "editor_help": (
            "Manual entry: one shortcut per line as shortcut<TAB>replacement. "
            "Removal: !shortcut. Import: .csv, .tsv, or .txt. "
            "Custom shortcuts append to the built-in list; same-key custom entries override existing values."
        ),
        "save_reload": "Save And Reload",
        "reload_file": "Reload File",
        "import_file": "Import File",
        "open_folder": "Open Folder",
        "close": "Close",
        "loaded_file": "Loaded {path}",
        "reloaded_file": "Reloaded {name}",
        "save_failed": "Save failed: {error}",
        "import_dialog_title": "Import shortcuts",
        "shortcut_files": "Shortcut files",
        "csv_files": "CSV files",
        "tsv_files": "TSV files",
        "text_files": "Text files",
        "all_files": "All files",
        "imported_count": "Imported {count} shortcut(s) from {path}. Save And Reload to apply.",
        "ctrl_alt_s_hint": "  |  Ctrl+Alt+S shortcuts",
        "keyboard_error": "Keyboard error in {source}. See {log_path}",
        "shortcuts_reloaded": "{mode_label} shortcuts reloaded from {path}",
        "custom_not_enabled": "Custom shortcut editing is not enabled.",
        "saved_reloaded": "Saved and reloaded {path}",
        "loaded_default_shortcuts_fix": (
            "{mode_label} loaded default shortcuts. Press Ctrl+Alt+S to fix: {error}"
        ),
        "app_description": "Clafrica+ Windows desktop keyboard",
        "mode_live_default": "Clafrica+",
        "mode_stable_default": "Clafrica+ Stable",
        "mode_live_custom": "Clafrica+ Custom",
        "mode_stable_custom": "Clafrica+ Custom Stable",
    },
}


def tr(language: str, key: str, **kwargs: object) -> str:
    text = UI_TEXTS.get(language, UI_TEXTS["en"])[key]
    return text.format(**kwargs) if kwargs else text


def acquire_single_instance_lock() -> None:
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.c_void_p,
    ]
    generic_read = 0x80000000
    file_share_none = 0
    open_always = 4
    invalid_handle = ctypes.c_void_p(-1).value
    handle = kernel32.CreateFileW(
        LOCK_PATH,
        generic_read,
        file_share_none,
        None,
        open_always,
        0,
        None,
    )
    if handle is None or handle == invalid_handle:
        print("Clafrica+ is already running.")
        sys.exit(0)
    globals()["_LOCK_HANDLE"] = handle


def get_foreground_window() -> int | None:
    hwnd = USER32.GetForegroundWindow()
    return int(hwnd) if hwnd else None


def set_foreground_window(hwnd: int | None) -> None:
    if hwnd:
        USER32.SetForegroundWindow(hwnd)


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("hwndActive", ctypes.c_void_p),
        ("hwndFocus", ctypes.c_void_p),
        ("hwndCapture", ctypes.c_void_p),
        ("hwndMenuOwner", ctypes.c_void_p),
        ("hwndMoveSize", ctypes.c_void_p),
        ("hwndCaret", ctypes.c_void_p),
        ("rcCaret", RECT),
    ]


def get_window_rect(hwnd: int | None) -> tuple[int, int, int, int] | None:
    if not hwnd:
        return None
    rect = RECT()
    ok = USER32.GetWindowRect(ctypes.wintypes.HWND(hwnd), ctypes.byref(rect))
    if not ok:
        return None
    return rect.left, rect.top, rect.right, rect.bottom


def get_caret_screen_point(hwnd: int | None) -> tuple[int, int] | None:
    if not hwnd:
        return None
    thread_id = USER32.GetWindowThreadProcessId(ctypes.wintypes.HWND(hwnd), None)
    if not thread_id:
        return None

    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(GUITHREADINFO)
    if not USER32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
        return None

    target_hwnd = (
        int(info.hwndCaret)
        if info.hwndCaret
        else int(info.hwndFocus)
        if info.hwndFocus
        else hwnd
    )
    if not target_hwnd:
        return None

    point = POINT(info.rcCaret.left, info.rcCaret.bottom)
    if not USER32.ClientToScreen(ctypes.wintypes.HWND(target_hwnd), ctypes.byref(point)):
        return None
    return point.x, point.y


def get_cursor_screen_point() -> tuple[int, int] | None:
    point = POINT()
    if not USER32.GetCursorPos(ctypes.byref(point)):
        return None
    return point.x, point.y


def event_to_typed_text(event) -> str | None:
    scan_code = int(getattr(event, "scan_code", 0) or 0)
    if not scan_code:
        name = event.name or ""
        return name if len(name) == 1 else None

    keyboard_state = (ctypes.c_ubyte * 256)()
    if not USER32.GetKeyboardState(ctypes.byref(keyboard_state)):
        name = event.name or ""
        return name if len(name) == 1 else None

    # GetKeyboardState is thread-local and may not reflect the current modifier
    # states when called from a non-message-loop thread (the keyboard library's
    # callback dispatcher).  Patch with GetAsyncKeyState so Shift+/ → "?" works.
    for _vk in _MODIFIER_VK_CODES:
        if USER32.GetAsyncKeyState(_vk) & 0x8000:
            keyboard_state[_vk] |= 0x80
        else:
            keyboard_state[_vk] &= 0x7F

    # Caps Lock is a toggle key. ToUnicodeEx reads the low bit for the toggle
    # state, so patch it from GetKeyState to avoid inverted capitalization.
    if USER32.GetKeyState(_VK_CAPITAL) & 0x0001:
        keyboard_state[_VK_CAPITAL] |= 0x01
    else:
        keyboard_state[_VK_CAPITAL] &= 0xFE

    virtual_key = USER32.MapVirtualKeyW(scan_code, MAPVK_VSC_TO_VK_EX)
    if not virtual_key:
        name = event.name or ""
        return name if len(name) == 1 else None

    buffer = ctypes.create_unicode_buffer(8)
    layout = USER32.GetKeyboardLayout(0)
    translated = USER32.ToUnicodeEx(
        virtual_key,
        scan_code,
        keyboard_state,
        buffer,
        len(buffer),
        0,
        layout,
    )
    if translated > 0:
        result = buffer.value[:translated]
        if len(result) == 1 and result.isalpha():
            shift_down = any(USER32.GetAsyncKeyState(vk) & 0x8000 for vk in (0x10, 0xA0, 0xA1))
            caps_on = bool(USER32.GetKeyState(_VK_CAPITAL) & 0x0001)
            return result.upper() if (caps_on ^ shift_down) else result.lower()
        return result

    name = event.name or ""
    return name if len(name) == 1 else None


@dataclass(frozen=True)
class Suggestion:
    word: str
    score: float


class PredictionClient:
    def __init__(self, base_url: str, timeout: tuple[int, int] = (5, 15)) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "nufi-windows-keyboard/1.0"})

    def fetch_suggestions(self, text: str, limit: int = 5, n: int = 4) -> list[Suggestion]:
        if not text.strip():
            return []
        response = self.session.post(
            f"{self.base_url}/api/keyboard/suggest",
            json={"text": text, "n": n, "limit": limit},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return [
            Suggestion(word=item["word"], score=float(item.get("score", 0.0)))
            for item in payload.get("suggestions", [])
        ]


_RESULAM_LOGO_PATH = r"G:\My Drive\Resulam\AI_Resulam\AI Background Resulam Nufi Bamileke Ndop Collection For NFT\resulam_logo_egg.png"


class SuggestionOverlay:
    def __init__(
        self,
        on_select: Callable[[int], None],
        on_quit: Callable[[], None],
        on_toggle: Callable[[], None] | None = None,
        on_edit_shortcuts: Callable[[], None] | None = None,
        on_toggle_language: Callable[[], None] | None = None,
        language: str = "fr",
    ) -> None:
        import tkinter as tk

        self._tk = tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#101216")
        self.root.wm_attributes("-alpha", 0.96)
        self._language = language
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._status_var = tk.StringVar(value="")
        self._hint_var = tk.StringVar(value="")
        self._state_var = tk.StringVar(value=tr(self._language, "on"))
        self._buttons: list[tk.Button] = []
        self._on_select = on_select
        self._on_quit = on_quit
        self._on_toggle = on_toggle
        self._on_edit_shortcuts = on_edit_shortcuts
        self._on_toggle_language = on_toggle_language
        self._enabled = True
        self._anchor_hwnd: int | None = None
        self._manual_position: tuple[int, int] | None = None
        self._drag_offset: tuple[int, int] | None = None
        self._drag_occurred: bool = False
        self._mode_label = "Clafrica+"
        self._logo_image = None  # keep reference to prevent GC

        self._frame = tk.Frame(self.root, bg="#101216", padx=8, pady=8)
        self._frame.pack(fill="both", expand=True)
        self._header = tk.Frame(self._frame, bg="#101216")
        self._header.pack(fill="x")

        # Logo (left side of header) — loaded with Pillow so we can resize it
        try:
            from PIL import Image, ImageTk
            img = Image.open(_RESULAM_LOGO_PATH).convert("RGBA")
            img.thumbnail((32, 32), Image.LANCZOS)
            self._logo_image = ImageTk.PhotoImage(img)
            self._logo_label = tk.Label(
                self._header,
                image=self._logo_image,
                bg="#101216",
                bd=0,
            )
            self._logo_label.pack(side="left", padx=(0, 6))
        except Exception:
            self._logo_label = None

        self._status = tk.Label(
            self._header,
            textvariable=self._status_var,
            fg="#d7dde8",
            bg="#101216",
            anchor="w",
            justify="left",
            font=("Segoe UI", 14),
        )
        self._status.pack(side="left", fill="x", expand=True)
        self._state = tk.Label(
            self._header,
            textvariable=self._state_var,
            fg="#ffffff",
            bg="#2a7a41",
            padx=8,
            pady=4,
            font=("Segoe UI", 11, "bold"),
        )
        self._exit_button = tk.Button(
            self._header,
            text=tr(self._language, "exit"),
            command=self._on_quit,
            bg="#8b2d2f",
            fg="#ffffff",
            activebackground="#a43a3d",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            font=("Segoe UI", 10, "bold"),
        )
        self._exit_button.pack(side="right")
        self._language_button = tk.Button(
            self._header,
            text=tr(self._language, "language_toggle"),
            command=self._handle_language_click,
            bg="#1d232d",
            fg="#f3f5f8",
            activebackground="#2b3340",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            font=("Segoe UI", 10, "bold"),
        )
        self._language_button.pack(side="right", padx=(0, 6))
        if self._on_edit_shortcuts is not None:
            self._edit_button = tk.Button(
                self._header,
                text=tr(self._language, "shortcuts"),
                command=self._on_edit_shortcuts,
                bg="#1d232d",
                fg="#f3f5f8",
                activebackground="#2b3340",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=10,
                pady=4,
                font=("Segoe UI", 10, "bold"),
            )
            self._edit_button.pack(side="right", padx=(0, 6))
        self._state.pack(side="right", padx=(0, 6))
        self._state.bind("<ButtonRelease-1>", self._handle_state_click)
        self._state.configure(cursor="hand2")
        self._hint = tk.Label(
            self._frame,
            textvariable=self._hint_var,
            fg="#ffd700",
            bg="#101216",
            anchor="w",
            justify="left",
            font=("Segoe UI", 11),
            wraplength=1100,
        )
        self._hint.pack(fill="x", pady=(4, 0))
        self._button_row = tk.Frame(self._frame, bg="#101216")
        self._button_row.pack(fill="x", pady=(6, 0))
        self._footer = tk.Label(
            self._frame,
            text=tr(self._language, "footer"),
            fg="#ffffff",
            bg="#101216",
            anchor="e",
            justify="right",
            font=("Segoe UI", 9),
        )
        self._footer.pack(fill="x", pady=(4, 0))
        draggable = [self._header, self._status, self._hint, self._state, self._footer]
        if self._logo_label is not None:
            draggable.append(self._logo_label)
        for widget in draggable:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag_window)
            widget.bind("<ButtonRelease-1>", self._end_drag)
        self.root.after(50, self._poll)

    @staticmethod
    def _caret_is_usable(
        caret: tuple[int, int] | None,
        window_rect: tuple[int, int, int, int] | None,
    ) -> bool:
        if caret is None:
            return False
        x, y = caret
        if window_rect is None:
            return x > 0 and y > 0
        left, top, right, bottom = window_rect
        margin = 24
        return (left - margin) <= x <= (right + margin) and (top - margin) <= y <= (bottom + margin)

    def _poll(self) -> None:
        while True:
            try:
                action, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            if action == "hide":
                self._render_idle(payload)
            elif action == "status":
                self._render_status(str(payload))
            elif action == "state":
                self._set_state(bool(payload))
            elif action == "language":
                self._apply_language(str(payload))
            elif action == "mode_label":
                self._mode_label = str(payload)
            elif action == "shortcut_hints":
                prefix, hints = payload
                self._render_shortcut_hints(str(prefix), list(hints))
            elif action == "suggestions":
                suggestions, hwnd = payload
                self._render_suggestions(suggestions, hwnd)
        self.root.after(50, self._poll)

    def _apply_clamped_geometry(self, x: int, y: int) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(8, min(x, screen_width - width - 8))
        y = max(8, min(y, screen_height - height - 8))
        self.root.geometry(f"+{x}+{y}")

    def _set_position(self, hwnd: int | None) -> None:
        if self._manual_position is not None:
            self._apply_clamped_geometry(*self._manual_position)
            return
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        cursor = get_cursor_screen_point()
        caret = get_caret_screen_point(hwnd)
        rect = get_window_rect(hwnd)
        if cursor is not None:
            x = cursor[0] + POINTER_OVERLAY_OFFSET_X
            y = cursor[1] + POINTER_OVERLAY_OFFSET_Y
        elif self._caret_is_usable(caret, rect):
            x = caret[0] + CARET_OVERLAY_OFFSET_X
            y = caret[1] + CARET_OVERLAY_OFFSET_Y
        elif rect is None:
            x = screen_width - width - 24
            y = screen_height - height - 24
        else:
            left, top, right, bottom = rect
            x = min(left + 48, max(left + 12, right - width - 24))
            y = min(bottom - height - 24, top + 64)

        self._apply_clamped_geometry(x, y)

    def _start_drag(self, event) -> None:
        self.root.update_idletasks()
        self._drag_offset = (
            int(event.x_root - self.root.winfo_x()),
            int(event.y_root - self.root.winfo_y()),
        )
        self._drag_occurred = False

    def _drag_window(self, event) -> None:
        if self._drag_offset is None:
            return
        self._drag_occurred = True
        x = int(event.x_root - self._drag_offset[0])
        y = int(event.y_root - self._drag_offset[1])
        self._manual_position = (x, y)
        self._apply_clamped_geometry(x, y)

    def _end_drag(self, event) -> None:
        was_drag = self._drag_occurred
        self._drag_offset = None
        self._drag_occurred = False
        if not was_drag and event.widget is self._state:
            self._handle_state_click(event)

    def _set_state(self, enabled: bool) -> None:
        self._enabled = enabled
        self._state_var.set(tr(self._language, "on") if enabled else tr(self._language, "off"))
        self._state.configure(bg="#2a7a41" if enabled else "#9b2d30")

    def _handle_state_click(self, _event) -> None:
        if self._on_toggle is not None:
            self._on_toggle()

    def _handle_language_click(self) -> None:
        if self._on_toggle_language is not None:
            self._on_toggle_language()

    def _apply_language(self, language: str) -> None:
        self._language = language
        self._exit_button.configure(text=tr(language, "exit"))
        self._language_button.configure(text=tr(language, "language_toggle"))
        if hasattr(self, "_edit_button"):
            self._edit_button.configure(text=tr(language, "shortcuts"))
        self._footer.configure(text=tr(language, "footer"))
        self._state_var.set(tr(language, "on") if self._enabled else tr(language, "off"))

    def set_language(self, language: str) -> None:
        self._queue.put(("language", language))

    def _format_shortcut_hints(self, prefix: str, hints: list[ShortcutHint]) -> str:
        if not prefix or not hints:
            return ""
        parts = [f"{prefix}[{hint.remaining}]" for hint in hints if hint.remaining]
        if not parts:
            return ""
        return tr(self._language, "shortcut_hint_prefix") + ", ".join(parts)

    def _render_shortcut_hints(self, prefix: str, hints: list[ShortcutHint]) -> None:
        text = self._format_shortcut_hints(prefix, hints)
        self._hint_var.set(text)

    def _render_idle(self, hwnd: int | None = None) -> None:
        self._anchor_hwnd = hwnd
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self._button_row.pack_forget()
        self._status_var.set(
            f"{self._mode_label} {tr(self._language, 'on')}  |  {tr(self._language, 'toggle_hint')}"
            if self._enabled
            else f"{self._mode_label} {tr(self._language, 'off')}  |  {tr(self._language, 'toggle_hint')}"
        )
        self._set_position(hwnd)
        self.root.deiconify()

    def _render_status(self, message: str) -> None:
        self._anchor_hwnd = None
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self._button_row.pack_forget()
        self._status_var.set(message)
        if message:
            self._set_position(None)
            self.root.deiconify()
        else:
            self._render_idle(None)

    def _render_suggestions(self, suggestions: list[Suggestion], hwnd: int | None) -> None:
        self._anchor_hwnd = hwnd
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        if not suggestions:
            self._render_idle(hwnd)
            return
        self._button_row.pack(fill="x", pady=(6, 0))
        self._status_var.set(tr(self._language, "suggestions_status"))
        for index, suggestion in enumerate(suggestions, start=1):
            button = self._tk.Button(
                self._button_row,
                text=f"{index}. {suggestion.word}",
                command=lambda idx=index - 1: self._on_select(idx),
                bg="#1d232d",
                fg="#f3f5f8",
                activebackground="#2b3340",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=16,
                pady=10,
                font=("Segoe UI", 14),
            )
            button.pack(side="left", padx=(0, 6))
            self._buttons.append(button)
        self._set_position(hwnd)
        self.root.deiconify()

    def show_status(self, message: str) -> None:
        self._queue.put(("status", message))

    def set_enabled_state(self, enabled: bool) -> None:
        self._queue.put(("state", enabled))

    def set_mode_label(self, label: str) -> None:
        self._queue.put(("mode_label", label))

    def show_shortcut_hints(self, prefix: str, hints: list[ShortcutHint]) -> None:
        self._queue.put(("shortcut_hints", (prefix, hints)))

    def show_suggestions(self, suggestions: list[Suggestion], hwnd: int | None) -> None:
        self._queue.put(("suggestions", (suggestions, hwnd)))

    def hide(self, hwnd: int | None = None) -> None:
        self._queue.put(("hide", hwnd))

    def run(self) -> None:
        self.root.mainloop()


class ShortcutEditorWindow:
    def __init__(
        self,
        root,
        shortcuts_path: Path,
        save_callback: Callable[[str], str],
        mode_label_provider: Callable[[], str],
        language: str,
        on_toggle_language: Callable[[], None],
    ) -> None:
        self.root = root
        self.shortcuts_path = shortcuts_path
        self.save_callback = save_callback
        self.mode_label_provider = mode_label_provider
        self.language = language
        self.on_toggle_language = on_toggle_language
        self._window = None
        self._text = None
        self._status_var = None
        self._title_label = None
        self._file_label = None
        self._help_label = None
        self._save_button = None
        self._reload_button = None
        self._import_button = None
        self._open_folder_button = None
        self._close_button = None
        self._language_button = None

    def show(self) -> None:
        if self._window is None or not self._window.winfo_exists():
            self._build()
        self._reload_from_disk(status_message=tr(self.language, "loaded_file", path=self.shortcuts_path))
        self._window.deiconify()
        self._window.lift()
        self._window.focus_force()

    def set_language(self, language: str) -> None:
        self.language = language
        if self._window is None or not self._window.winfo_exists():
            return
        self._apply_language()

    def _build(self) -> None:
        import tkinter as tk

        self._window = tk.Toplevel(self.root)
        self._window.title(tr(self.language, "editor_title", mode_label=self.mode_label_provider()))
        self._window.geometry("960x680")
        self._window.configure(bg="#101216")
        self._window.protocol("WM_DELETE_WINDOW", self._window.withdraw)

        frame = tk.Frame(self._window, bg="#101216", padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        title_row = tk.Frame(frame, bg="#101216")
        title_row.pack(fill="x")

        self._title_label = tk.Label(
            title_row,
            text="",
            fg="#f3f5f8",
            bg="#101216",
            anchor="w",
            font=("Segoe UI", 15, "bold"),
        )
        self._title_label.pack(side="left", fill="x", expand=True)
        self._language_button = tk.Button(
            title_row,
            text="",
            command=self.on_toggle_language,
            bg="#1d232d",
            fg="#f3f5f8",
            activebackground="#2b3340",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        self._language_button.pack(side="right")
        self._file_label = tk.Label(
            frame,
            text="",
            fg="#b6c0cf",
            bg="#101216",
            anchor="w",
            justify="left",
            font=("Segoe UI", 10),
        )
        self._file_label.pack(fill="x", pady=(6, 0))
        self._help_label = tk.Label(
            frame,
            text="",
            fg="#ffd700",
            bg="#101216",
            anchor="w",
            justify="left",
            font=("Segoe UI", 10),
        )
        self._help_label.pack(fill="x", pady=(6, 10))

        text_frame = tk.Frame(frame, bg="#101216")
        text_frame.pack(fill="both", expand=True)

        y_scroll = tk.Scrollbar(text_frame)
        y_scroll.pack(side="right", fill="y")
        x_scroll = tk.Scrollbar(text_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self._text = tk.Text(
            text_frame,
            wrap="none",
            undo=True,
            bg="#161b22",
            fg="#f3f5f8",
            insertbackground="#f3f5f8",
            selectbackground="#2b3340",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            font=("Consolas", 11),
            padx=12,
            pady=12,
        )
        self._text.pack(fill="both", expand=True)
        y_scroll.config(command=self._text.yview)
        x_scroll.config(command=self._text.xview)

        button_row = tk.Frame(frame, bg="#101216")
        button_row.pack(fill="x", pady=(12, 0))

        self._save_button = tk.Button(
            button_row,
            text="",
            command=self._save,
            bg="#2a7a41",
            fg="#ffffff",
            activebackground="#348f4f",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        self._save_button.pack(side="left")
        self._reload_button = tk.Button(
            button_row,
            text="",
            command=self._reload_from_disk,
            bg="#1d232d",
            fg="#f3f5f8",
            activebackground="#2b3340",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        self._reload_button.pack(side="left", padx=(8, 0))
        self._import_button = tk.Button(
            button_row,
            text="",
            command=self._import_file,
            bg="#1d232d",
            fg="#f3f5f8",
            activebackground="#2b3340",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        self._import_button.pack(side="left", padx=(8, 0))
        self._open_folder_button = tk.Button(
            button_row,
            text="",
            command=self._open_folder,
            bg="#1d232d",
            fg="#f3f5f8",
            activebackground="#2b3340",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        self._open_folder_button.pack(side="left", padx=(8, 0))
        self._close_button = tk.Button(
            button_row,
            text="",
            command=self._window.withdraw,
            bg="#8b2d2f",
            fg="#ffffff",
            activebackground="#a43a3d",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        self._close_button.pack(side="right")

        self._status_var = tk.StringVar(value="")
        tk.Label(
            frame,
            textvariable=self._status_var,
            fg="#b6c0cf",
            bg="#101216",
            anchor="w",
            justify="left",
            font=("Segoe UI", 10),
        ).pack(fill="x", pady=(10, 0))
        self._apply_language()

    def _apply_language(self) -> None:
        self._window.title(tr(self.language, "editor_title", mode_label=self.mode_label_provider()))
        self._title_label.configure(text=tr(self.language, "editor_heading"))
        self._file_label.configure(text=tr(self.language, "file_label", path=self.shortcuts_path))
        self._help_label.configure(text=tr(self.language, "editor_help"))
        self._save_button.configure(text=tr(self.language, "save_reload"))
        self._reload_button.configure(text=tr(self.language, "reload_file"))
        self._import_button.configure(text=tr(self.language, "import_file"))
        self._open_folder_button.configure(text=tr(self.language, "open_folder"))
        self._close_button.configure(text=tr(self.language, "close"))
        self._language_button.configure(text=tr(self.language, "language_toggle"))

    def _reload_from_disk(self, status_message: str | None = None) -> None:
        ensure_shortcuts_file(self.shortcuts_path)
        text = self.shortcuts_path.read_text(encoding="utf-8")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)
        self._status_var.set(
            status_message or tr(self.language, "reloaded_file", name=self.shortcuts_path.name)
        )

    def _save(self) -> None:
        text = self._text.get("1.0", "end")
        try:
            message = self.save_callback(text)
        except ShortcutFileError as exc:
            self._status_var.set(str(exc))
            return
        except Exception as exc:
            self._status_var.set(tr(self.language, "save_failed", error=exc))
            return
        self._status_var.set(message)

    def _import_file(self) -> None:
        from tkinter import filedialog

        selected = filedialog.askopenfilename(
            title=tr(self.language, "import_dialog_title"),
            filetypes=[
                (tr(self.language, "shortcut_files"), "*.csv *.tsv *.txt"),
                (tr(self.language, "csv_files"), "*.csv"),
                (tr(self.language, "tsv_files"), "*.tsv"),
                (tr(self.language, "text_files"), "*.txt"),
                (tr(self.language, "all_files"), "*.*"),
            ],
        )
        if not selected:
            return
        try:
            current = parse_shortcuts_text(self._text.get("1.0", "end"))
            imported = load_import_shortcuts(Path(selected))
        except ShortcutFileError as exc:
            self._status_var.set(str(exc))
            return
        merged = dict(current)
        merged.update(imported)
        self._text.delete("1.0", "end")
        self._text.insert("1.0", render_shortcuts_text(merged))
        self._status_var.set(tr(self.language, "imported_count", count=len(imported), path=selected))

    def _open_folder(self) -> None:
        ensure_shortcuts_file(self.shortcuts_path)
        os.startfile(str(self.shortcuts_path.parent))


class GlobalNufiWindowsKeyboard:
    def __init__(
        self,
        api_base_url: str,
        suggestion_limit: int = 5,
        suggestion_delay_ms: int = 250,
        live_transform: bool = True,
        custom_shortcuts_path: Path | None = None,
        allow_shortcut_editing: bool = False,
        open_shortcut_editor_on_start: bool = False,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.suggestion_limit = suggestion_limit
        self.suggestion_delay_ms = suggestion_delay_ms
        self.live_transform = live_transform
        self.ui_language = "fr"
        self.allow_shortcut_editing = allow_shortcut_editing
        self.custom_shortcuts_path = (
            custom_shortcuts_path
            if custom_shortcuts_path is not None
            else get_user_shortcuts_path()
            if allow_shortcut_editing
            else None
        )
        self.open_shortcut_editor_on_start = open_shortcut_editor_on_start
        self.mode_label = self._build_mode_label()
        self.shortcut_load_error: str | None = None
        self.engine = self._build_engine()
        self.predictor = PredictionClient(self.api_base_url)
        self.enabled = True
        self.recent_shift_release_time = 0.0
        self.ctrl_active = False
        self.alt_active = False
        self.win_active = False
        self.quit_requested = threading.Event()
        self.handling_injection = False
        self.lock = threading.RLock()
        self.overlay = SuggestionOverlay(
            self.select_suggestion,
            self.quit_requested.set,
            self._toggle_enabled,
            self.open_shortcut_editor if self.allow_shortcut_editing else None,
            self._toggle_ui_language,
            self.ui_language,
        )
        self.overlay.set_mode_label(self.mode_label)
        self.shortcut_editor = (
            ShortcutEditorWindow(
                self.overlay.root,
                self.custom_shortcuts_path,
                self._save_custom_shortcuts,
                self._build_mode_label,
                self.ui_language,
                self._toggle_ui_language,
            )
            if self.allow_shortcut_editing and self.custom_shortcuts_path is not None
            else None
        )
        self.active_hwnd: int | None = None
        self.committed_context = ""
        self.pending_phrase_raw = ""
        self.raw_token = ""
        self.displayed_active_text = ""
        self.latest_suggestions: list[Suggestion] = []
        self.latest_shortcut_hints: list[ShortcutHint] = []
        self.fetch_generation = 0
        self.fetch_timer: threading.Timer | None = None
        self._mouse_down = False
        self._last_shift_down_time = 0.0
        self._suppress_toggle_until = 0.0

    def _build_mode_label(self) -> str:
        if self.allow_shortcut_editing:
            return (
                tr(self.ui_language, "mode_live_custom")
                if self.live_transform
                else tr(self.ui_language, "mode_stable_custom")
            )
        return (
            tr(self.ui_language, "mode_live_default")
            if self.live_transform
            else tr(self.ui_language, "mode_stable_default")
        )

    def _build_engine(self) -> NufiTransformEngine:
        if self.custom_shortcuts_path is None:
            self.shortcut_load_error = None
            return NufiTransformEngine()
        ensure_shortcuts_file(self.custom_shortcuts_path)
        try:
            engine = NufiTransformEngine(custom_shortcuts_path=self.custom_shortcuts_path)
        except ShortcutFileError as exc:
            self.shortcut_load_error = str(exc)
            return NufiTransformEngine()
        self.shortcut_load_error = None
        return engine

    @staticmethod
    def _is_shift_event(event) -> bool:
        name = (event.name or "").lower()
        if name in SHIFT_KEYS or "shift" in name:
            return True
        return event.scan_code in SHIFT_SCAN_CODES

    @staticmethod
    def _normalize_query(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _trim_context(self, text: str, max_chars: int = 240) -> str:
        return text[-max_chars:]

    def _is_phrase_prefix(self, text: str) -> bool:
        if not text:
            return False
        return any(key.startswith(text) for key in self.engine.phrase_map.keys())

    def _reset_state(self) -> None:
        self.committed_context = ""
        self.pending_phrase_raw = ""
        self.raw_token = ""
        self.displayed_active_text = ""
        self.latest_suggestions = []
        self.latest_shortcut_hints = []
        self.overlay.show_shortcut_hints("", [])
        self.overlay.hide(self.active_hwnd)

    def _modifier_combo_active(self) -> bool:
        return self.ctrl_active or self.alt_active or self.win_active

    def _current_shortcut_prefix(self) -> str:
        return self.pending_phrase_raw + self.raw_token

    def _status_text(self, enabled: bool) -> str:
        state = tr(self.ui_language, "on") if enabled else tr(self.ui_language, "off")
        suffix = tr(self.ui_language, "ctrl_alt_s_hint") if self.allow_shortcut_editing else ""
        return f"{self.mode_label} {state}  |  {tr(self.ui_language, 'toggle_hint')}{suffix}"

    def _visible_active_text(self) -> str:
        if self.live_transform:
            return self.displayed_active_text
        return self.pending_phrase_raw + self.raw_token

    def _live_mapped_text(self, raw_text: str) -> str:
        if not raw_text:
            return ""
        return self.engine.apply_mapping(raw_text, preserve_ambiguous_trailing_token=True)

    def _update_shortcut_hints(self) -> None:
        prefix = self._current_shortcut_prefix()
        hints = self.engine.get_shortcut_hints(prefix, limit=6) if prefix else []
        self.latest_shortcut_hints = hints
        self.overlay.show_shortcut_hints(prefix, hints)

    def _record_exception(self, source: str, exc: Exception) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {source}: {exc}\n")
            handle.write(traceback.format_exc())
            handle.write("\n")
        self.overlay.show_status(tr(self.ui_language, "keyboard_error", source=source, log_path=LOG_PATH))

    def _reload_engine_from_disk(self) -> None:
        self.engine = self._build_engine()
        self._update_shortcut_hints()
        if self.latest_suggestions:
            self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
        else:
            self.overlay.hide(self.active_hwnd)
        self.overlay.show_status(
            tr(
                self.ui_language,
                "shortcuts_reloaded",
                mode_label=self.mode_label,
                path=self.custom_shortcuts_path,
            )
        )

    def _save_custom_shortcuts(self, text: str) -> str:
        if self.custom_shortcuts_path is None:
            raise ShortcutFileError(tr(self.ui_language, "custom_not_enabled"))
        save_shortcuts_text(self.custom_shortcuts_path, text)
        with self.lock:
            self._reload_engine_from_disk()
        return tr(self.ui_language, "saved_reloaded", path=self.custom_shortcuts_path)

    def open_shortcut_editor(self) -> None:
        if self.shortcut_editor is None:
            return
        self.overlay.root.after(0, self.shortcut_editor.show)

    def _toggle_ui_language(self) -> None:
        self.ui_language = "en" if self.ui_language == "fr" else "fr"
        self.mode_label = self._build_mode_label()
        self.overlay.set_language(self.ui_language)
        self.overlay.set_mode_label(self.mode_label)
        if self.shortcut_editor is not None:
            self.overlay.root.after(0, lambda: self.shortcut_editor.set_language(self.ui_language))
        self._refresh_language_view()

    def _refresh_language_view(self) -> None:
        self._update_shortcut_hints()
        if self.shortcut_load_error:
            self.overlay.show_status(
                tr(
                    self.ui_language,
                    "loaded_default_shortcuts_fix",
                    mode_label=self.mode_label,
                    error=self.shortcut_load_error,
                )
            )
            return
        if self.latest_suggestions:
            self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
            return
        self.overlay.show_status(self._status_text(self.enabled))

    @staticmethod
    def _is_any_mouse_button_down() -> bool:
        return any(
            USER32.GetAsyncKeyState(vk) & 0x8000
            for vk in (VK_LBUTTON, VK_RBUTTON, VK_MBUTTON)
        )

    def _watch_for_mouse_activity(self) -> None:
        while not self.quit_requested.wait(0.05):
            mouse_down = self._is_any_mouse_button_down()
            if mouse_down and not self._mouse_down:
                with self.lock:
                    if self.live_transform and (
                        self.raw_token or self.pending_phrase_raw or self.displayed_active_text
                    ):
                        self._reset_state()
            self._mouse_down = mouse_down

    def _replace_visible_text(self, source_visible: str, replacement_visible: str) -> None:
        import keyboard

        self.recent_shift_release_time = 0.0
        self._suppress_toggle_until = time.monotonic() + POST_INJECTION_TOGGLE_GUARD_SECONDS
        self.handling_injection = True
        try:
            for _ in range(len(source_visible)):
                keyboard.send("backspace")
            if replacement_visible:
                keyboard.write(replacement_visible, delay=0)
        finally:
            self.handling_injection = False

    def _visible_query_text(self) -> str:
        if self.live_transform:
            live_text = self.committed_context + self._visible_active_text()
        else:
            live_text = self.committed_context + self.pending_phrase_raw + self.engine.apply_mapping(
                self.raw_token,
                preserve_ambiguous_trailing_token=True,
            )
        return self._normalize_query(live_text)

    def _try_auto_complete_current_entry(self) -> bool:
        if self.live_transform:
            return False
        combined_raw = self.pending_phrase_raw + self.raw_token
        completed = self.engine.auto_complete_exact_text(combined_raw)
        if not completed or completed == combined_raw:
            return False

        self._replace_visible_text(combined_raw, completed)
        self.committed_context = self._trim_context(self.committed_context + completed)
        self.pending_phrase_raw = ""
        self.raw_token = ""
        self._update_shortcut_hints()
        if self.latest_suggestions:
            self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
        self._schedule_suggestion_fetch()
        return True

    def _apply_live_transform_after_input(self, appended_visible: str = "") -> None:
        raw_text = self.pending_phrase_raw + self.raw_token
        previous_visible = self.displayed_active_text
        current_visible = previous_visible + appended_visible
        next_visible = self._live_mapped_text(raw_text)
        if current_visible != next_visible:
            self._replace_visible_text(current_visible, next_visible)
        self.displayed_active_text = next_visible

    def _apply_live_transform_after_backspace(self) -> None:
        raw_text = self.pending_phrase_raw + self.raw_token
        previous_visible = self.displayed_active_text
        current_visible = previous_visible[:-1] if previous_visible else ""
        next_visible = self._live_mapped_text(raw_text)
        if current_visible != next_visible:
            self._replace_visible_text(current_visible, next_visible)
        self.displayed_active_text = next_visible

    def _finalized_visible_text(self, source_raw: str, delimiter_visible: str) -> str:
        finalized_raw = self.engine.finalize_input(source_raw)
        if not self.live_transform:
            return finalized_raw
        combined_raw = self.pending_phrase_raw + self.raw_token
        visible_active = self._visible_active_text()
        if finalized_raw != source_raw:
            return finalized_raw
        if visible_active and visible_active != combined_raw:
            return visible_active + delimiter_visible
        return finalized_raw

    def _should_use_digit_for_suggestion(self, digit_text: str) -> bool:
        if digit_text not in {"1", "2", "3", "4", "5"} or not self.latest_suggestions:
            return False

        combined_raw = self.pending_phrase_raw + self.raw_token
        if combined_raw.endswith(("'", "’")):
            index = int(digit_text) - 1
            return index < len(self.latest_suggestions)
        # In live-transform mode the displayed text already differs from
        # the raw token (e.g. n2 renders to tone char). Use visible text
        # so a following digit like 1 is not blocked as a transform key.
        check_text = (
            self.displayed_active_text
            if self.live_transform and self.displayed_active_text
            else combined_raw
        )
        if check_text and self.engine.would_transform_with_appended_text(check_text, digit_text):
            return False

        index = int(digit_text) - 1
        return index < len(self.latest_suggestions)

    def _schedule_suggestion_fetch(self) -> None:
        if not self.enabled:
            self.overlay.hide(self.active_hwnd)
            return
        query = self._visible_query_text()
        if not query:
            self.latest_suggestions = []
            self.overlay.hide(self.active_hwnd)
            return
        self.fetch_generation += 1
        generation = self.fetch_generation
        hwnd = self.active_hwnd
        if self.fetch_timer is not None:
            self.fetch_timer.cancel()
        self.fetch_timer = threading.Timer(
            self.suggestion_delay_ms / 1000.0,
            self._fetch_suggestions_worker,
            args=(generation, query, hwnd),
        )
        self.fetch_timer.daemon = True
        self.fetch_timer.start()

    def _fetch_suggestions_worker(self, generation: int, query: str, hwnd: int | None) -> None:
        try:
            suggestions = self.predictor.fetch_suggestions(query, limit=self.suggestion_limit)
        except Exception:
            suggestions = []
        with self.lock:
            if generation != self.fetch_generation:
                return
            if suggestions:
                self.latest_suggestions = suggestions
                overlay_suggestions = suggestions
            else:
                overlay_suggestions = list(self.latest_suggestions)
        if overlay_suggestions:
            self.overlay.show_suggestions(overlay_suggestions, hwnd)
        else:
            self.overlay.hide()

    def _finalize_current_token_with_delimiter(self, delimiter_visible: str) -> None:
        combined_raw = self.pending_phrase_raw + self.raw_token

        if delimiter_visible.isspace() and self._is_phrase_prefix(combined_raw + delimiter_visible):
            source_visible = self._visible_active_text() + delimiter_visible
            self.pending_phrase_raw += self.raw_token + delimiter_visible
            self.raw_token = ""
            if self.live_transform:
                next_visible = self._live_mapped_text(self.pending_phrase_raw)
                if source_visible != next_visible:
                    self._replace_visible_text(source_visible, next_visible)
                self.displayed_active_text = next_visible
            self._update_shortcut_hints()
            if self.latest_suggestions:
                self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
            self._schedule_suggestion_fetch()
            return

        source_visible = self._visible_active_text() + delimiter_visible
        source_raw = combined_raw + delimiter_visible
        replacement_visible = self._finalized_visible_text(source_raw, delimiter_visible)

        if replacement_visible != source_visible:
            self._replace_visible_text(source_visible, replacement_visible)
        self.committed_context = self._trim_context(self.committed_context + replacement_visible)
        self.pending_phrase_raw = ""
        self.raw_token = ""
        self.displayed_active_text = ""
        self._update_shortcut_hints()
        if self.latest_suggestions:
            self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
        self._schedule_suggestion_fetch()

    def _handle_printable_key(self, name: str) -> None:
        self.raw_token += name
        if self._try_auto_complete_current_entry():
            return
        if self.live_transform:
            self._apply_live_transform_after_input(name)
        self._update_shortcut_hints()
        self._schedule_suggestion_fetch()

    def _handle_backspace(self) -> None:
        if self.raw_token:
            self.raw_token = self.raw_token[:-1]
            if self.live_transform:
                self._apply_live_transform_after_backspace()
            self._update_shortcut_hints()
            self._schedule_suggestion_fetch()
            return
        if self.pending_phrase_raw:
            self.pending_phrase_raw = self.pending_phrase_raw[:-1]
            if self.live_transform:
                self._apply_live_transform_after_backspace()
            self._update_shortcut_hints()
            self._schedule_suggestion_fetch()
            return
        if self.committed_context:
            self.committed_context = self.committed_context[:-1]
        self._update_shortcut_hints()
        self._schedule_suggestion_fetch()

    def select_suggestion(self, index: int, remove_typed_digit: bool = False) -> None:
        with self.lock:
            if index < 0 or index >= len(self.latest_suggestions):
                return
            suggestion = self.latest_suggestions[index]
            hwnd = self.active_hwnd
            combined_raw = self.pending_phrase_raw + self.raw_token
        set_foreground_window(hwnd)
        time.sleep(0.05)
        with self.lock:
            if remove_typed_digit:
                self._suppress_toggle_until = time.monotonic() + POST_INJECTION_TOGGLE_GUARD_SECONDS
                self.handling_injection = True
                try:
                    import keyboard

                    keyboard.send("backspace")
                finally:
                    self.handling_injection = False

            if combined_raw:
                finalized = self.engine.finalize_input(combined_raw)
                replacement = f"{finalized} {suggestion.word} "
                self._replace_visible_text(self._visible_active_text(), replacement)
                self.committed_context = self._trim_context(
                    self.committed_context + replacement
                )
                self.pending_phrase_raw = ""
                self.raw_token = ""
                self.displayed_active_text = ""
                self._update_shortcut_hints()
            else:
                needs_space = bool(self.committed_context and not self.committed_context[-1].isspace())
                insertion = f"{' ' if needs_space else ''}{suggestion.word} "
                self._suppress_toggle_until = time.monotonic() + POST_INJECTION_TOGGLE_GUARD_SECONDS
                self.handling_injection = True
                try:
                    import keyboard

                    keyboard.write(insertion, delay=0)
                finally:
                    self.handling_injection = False
                self.committed_context = self._trim_context(self.committed_context + insertion)
                self._update_shortcut_hints()
            self._schedule_suggestion_fetch()

    def _schedule_digit_selection(self, index: int) -> None:
        timer = threading.Timer(0.03, lambda: self.select_suggestion(index, remove_typed_digit=True))
        timer.daemon = True
        timer.start()

    def _toggle_enabled(self) -> None:
        self.enabled = not self.enabled
        self.overlay.set_enabled_state(self.enabled)
        if not self.enabled:
            self._reset_state()
            self.overlay.show_status(self._status_text(False))
        else:
            self.overlay.show_status(self._status_text(True))
            self._schedule_suggestion_fetch()

    def _handle_double_shift_toggle(self, event) -> None:
        now = time.monotonic()
        if self.handling_injection or now < self._suppress_toggle_until:
            return
        if event.event_type == "down" and self._is_shift_event(event):
            self._last_shift_down_time = now
            return
        if event.event_type != "up":
            return
        if not self._is_shift_event(event):
            return
        if now - self._last_shift_down_time > 0.35:
            return
        if now - self.recent_shift_release_time <= TOGGLE_WINDOW_SECONDS:
            with self.lock:
                self._toggle_enabled()
                self.recent_shift_release_time = 0.0
            return
        self.recent_shift_release_time = now

    def _handle_key_event(self, event) -> None:
        if self.handling_injection:
            return

        name = event.name or ""
        lowered = name.lower()
        typed_text = event_to_typed_text(event)

        if lowered in {"ctrl", "left ctrl", "right ctrl"}:
            self.ctrl_active = event.event_type == "down"
            return
        if lowered in {"alt", "left alt", "right alt"}:
            self.alt_active = event.event_type == "down"
            return
        if lowered in {"windows", "left windows", "right windows"}:
            self.win_active = event.event_type == "down"
            return
        if event.event_type != "down":
            return

        self.active_hwnd = get_foreground_window()
        with self.lock:
            if not self.enabled:
                return
            if self._modifier_combo_active():
                if self.latest_suggestions:
                    self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
                else:
                    self.overlay.hide(self.active_hwnd)
                return
            if lowered in SHIFT_KEYS:
                return
            if self._should_use_digit_for_suggestion(typed_text or ""):
                self._schedule_digit_selection(int(typed_text) - 1)
                return
            if lowered == "backspace":
                self._handle_backspace()
                return
            if lowered in NAVIGATION_KEYS:
                self._reset_state()
                return
            if lowered in DELIMITER_KEYS:
                delimiter = DELIMITER_KEYS[lowered]
                if self.raw_token:
                    self._finalize_current_token_with_delimiter(delimiter)
                else:
                    self.committed_context = self._trim_context(self.committed_context + delimiter)
                    self._schedule_suggestion_fetch()
                return
            if typed_text in PUNCTUATION_DELIMITERS:
                self.raw_token += typed_text
                if self._try_auto_complete_current_entry():
                    return
                self.raw_token = self.raw_token[:-len(typed_text)]
                if self.raw_token:
                    self._finalize_current_token_with_delimiter(typed_text)
                else:
                    self.committed_context = self._trim_context(self.committed_context + typed_text)
                    self._schedule_suggestion_fetch()
                return
            if typed_text:
                self._handle_printable_key(typed_text)
                return
            if lowered not in MODIFIER_KEYS:
                self._reset_state()

    def run(self) -> None:
        import keyboard

        acquire_single_instance_lock()
        keyboard.hook(self._safe_handle_double_shift_toggle)
        keyboard.hook(self._safe_handle_key_event)
        keyboard.add_hotkey("ctrl+alt+q", self.quit_requested.set)
        if self.allow_shortcut_editing:
            keyboard.add_hotkey("ctrl+alt+s", self.open_shortcut_editor)
        for index in range(self.suggestion_limit):
            keyboard.add_hotkey(
                f"ctrl+shift+{index + 1}",
                lambda idx=index: self.select_suggestion(idx),
            )
        self.overlay.set_enabled_state(True)
        if self.shortcut_load_error:
            self.overlay.show_status(
                tr(
                    self.ui_language,
                    "loaded_default_shortcuts_fix",
                    mode_label=self.mode_label,
                    error=self.shortcut_load_error,
                )
            )
        else:
            self.overlay.show_status(self._status_text(True))
        if self.open_shortcut_editor_on_start or self.shortcut_load_error:
            self.open_shortcut_editor()

        watcher = threading.Thread(target=self._watch_for_quit, daemon=True)
        watcher.start()
        mouse_watcher = threading.Thread(target=self._watch_for_mouse_activity, daemon=True)
        mouse_watcher.start()
        self.overlay.run()

    def _safe_handle_double_shift_toggle(self, event) -> None:
        try:
            self._handle_double_shift_toggle(event)
        except Exception as exc:
            self._record_exception("toggle", exc)

    def _safe_handle_key_event(self, event) -> None:
        try:
            self._handle_key_event(event)
        except Exception as exc:
            self._record_exception("key", exc)

    def _watch_for_quit(self) -> None:
        while not self.quit_requested.wait(0.25):
            pass
        self.overlay.root.after(0, self.overlay.root.destroy)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=tr("fr", "app_description"))
    parser.add_argument(
        "--api-base-url",
        default="https://nufi-gen-ai-dug3ggdsh3fze9e5.canadacentral-01.azurewebsites.net",
        help="Prediction API base URL, without trailing slash.",
    )
    parser.add_argument(
        "--suggestion-limit",
        type=int,
        default=5,
        choices=range(1, 6),
        help="How many next-word suggestions to show.",
    )
    parser.add_argument(
        "--suggestion-delay-ms",
        type=int,
        default=250,
        help="Debounce delay before calling the prediction API.",
    )
    parser.add_argument(
        "--live-transform",
        action="store_true",
        default=True,
        help="Rewrite the active shortcut as you type.",
    )
    parser.add_argument(
        "--stable-transform",
        dest="live_transform",
        action="store_false",
        help="Use the old finalize-on-space behavior.",
    )
    parser.add_argument(
        "--customizable",
        action="store_true",
        help="Load user shortcuts from AppData and enable the shortcut editor.",
    )
    parser.add_argument(
        "--custom-shortcuts-file",
        type=Path,
        help="Override the custom shortcuts file path for the customizable build.",
    )
    parser.add_argument(
        "--edit-shortcuts",
        action="store_true",
        help="Open the shortcut editor on startup.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    app = GlobalNufiWindowsKeyboard(
        api_base_url=args.api_base_url,
        suggestion_limit=args.suggestion_limit,
        suggestion_delay_ms=args.suggestion_delay_ms,
        live_transform=args.live_transform,
        custom_shortcuts_path=args.custom_shortcuts_file,
        allow_shortcut_editing=(
            args.customizable
            or args.custom_shortcuts_file is not None
            or args.edit_shortcuts
        ),
        open_shortcut_editor_on_start=args.edit_shortcuts,
    )
    app.run()
    return 0
