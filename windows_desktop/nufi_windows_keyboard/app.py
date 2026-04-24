from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
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

from .engine import NufiTransformEngine


USER32 = ctypes.windll.user32
MAPVK_VSC_TO_VK_EX = 3
LOCK_PATH = str(Path(tempfile.gettempdir()) / "ClafricaPlus.lock")
LOG_PATH = str(Path(tempfile.gettempdir()) / "ClafricaPlus.log")
TOGGLE_WINDOW_SECONDS = 0.35
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
        print("Nufi Windows keyboard is already running.")
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


class SuggestionOverlay:
    def __init__(self, on_select: Callable[[int], None]) -> None:
        import tkinter as tk

        self._tk = tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#101216")
        self.root.wm_attributes("-alpha", 0.96)
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._status_var = tk.StringVar(value="")
        self._state_var = tk.StringVar(value="ON")
        self._buttons: list[tk.Button] = []
        self._on_select = on_select
        self._enabled = True

        self._frame = tk.Frame(self.root, bg="#101216", padx=8, pady=8)
        self._frame.pack(fill="both", expand=True)
        self._header = tk.Frame(self._frame, bg="#101216")
        self._header.pack(fill="x")
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
        self._state.pack(side="right")
        self._button_row = tk.Frame(self._frame, bg="#101216")
        self._button_row.pack(fill="x", pady=(6, 0))
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
            elif action == "suggestions":
                suggestions, hwnd = payload
                self._render_suggestions(suggestions, hwnd)
        self.root.after(50, self._poll)

    def _set_position(self, hwnd: int | None) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        caret = get_caret_screen_point(hwnd)
        rect = get_window_rect(hwnd)
        if self._caret_is_usable(caret, rect):
            x = caret[0] + 14
            y = caret[1] + 12
        elif rect is None:
            x = screen_width - width - 24
            y = screen_height - height - 24
        else:
            left, top, right, bottom = rect
            x = min(left + 48, max(left + 12, right - width - 24))
            y = min(bottom - height - 24, top + 64)

        x = max(8, min(x, screen_width - width - 8))
        y = max(8, min(y, screen_height - height - 8))
        self.root.geometry(f"+{x}+{y}")

    def _set_state(self, enabled: bool) -> None:
        self._enabled = enabled
        self._state_var.set("ON" if enabled else "OFF")
        self._state.configure(bg="#2a7a41" if enabled else "#9b2d30")

    def _render_idle(self, hwnd: int | None = None) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self._button_row.pack_forget()
        self._status_var.set("Nufi keyboard ON" if self._enabled else "Nufi keyboard OFF")
        self._set_position(hwnd)
        self.root.deiconify()

    def _render_status(self, message: str) -> None:
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
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        if not suggestions:
            self._render_idle(hwnd)
            return
        self._button_row.pack(fill="x", pady=(6, 0))
        self._status_var.set("Suggestions  1..5 or Ctrl+Shift+1..5")
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

    def show_suggestions(self, suggestions: list[Suggestion], hwnd: int | None) -> None:
        self._queue.put(("suggestions", (suggestions, hwnd)))

    def hide(self, hwnd: int | None = None) -> None:
        self._queue.put(("hide", hwnd))

    def run(self) -> None:
        self.root.mainloop()


class GlobalNufiWindowsKeyboard:
    def __init__(
        self,
        api_base_url: str,
        suggestion_limit: int = 5,
        suggestion_delay_ms: int = 250,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.suggestion_limit = suggestion_limit
        self.suggestion_delay_ms = suggestion_delay_ms
        self.engine = NufiTransformEngine()
        self.predictor = PredictionClient(self.api_base_url)
        self.enabled = True
        self.recent_shift_release_time = 0.0
        self.ctrl_active = False
        self.alt_active = False
        self.win_active = False
        self.quit_requested = threading.Event()
        self.handling_injection = False
        self.lock = threading.RLock()
        self.overlay = SuggestionOverlay(self.select_suggestion)
        self.active_hwnd: int | None = None
        self.committed_context = ""
        self.pending_phrase_raw = ""
        self.raw_token = ""
        self.latest_suggestions: list[Suggestion] = []
        self.fetch_generation = 0
        self.fetch_timer: threading.Timer | None = None

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
        self.latest_suggestions = []
        self.overlay.hide(self.active_hwnd)

    def _modifier_combo_active(self) -> bool:
        return self.ctrl_active or self.alt_active or self.win_active

    def _record_exception(self, source: str, exc: Exception) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {source}: {exc}\n")
            handle.write(traceback.format_exc())
            handle.write("\n")
        self.overlay.show_status(f"Keyboard error in {source}. See {LOG_PATH}")

    def _replace_visible_text(self, source_visible: str, replacement_visible: str) -> None:
        import keyboard

        self.handling_injection = True
        try:
            for _ in range(len(source_visible)):
                keyboard.send("backspace")
            if replacement_visible:
                keyboard.write(replacement_visible, delay=0)
        finally:
            self.handling_injection = False

    def _visible_query_text(self) -> str:
        live_text = self.committed_context + self.pending_phrase_raw + self.engine.apply_mapping(
            self.raw_token,
            preserve_ambiguous_trailing_token=True,
        )
        return self._normalize_query(live_text)

    def _try_auto_complete_current_entry(self) -> bool:
        combined_raw = self.pending_phrase_raw + self.raw_token
        completed = self.engine.auto_complete_exact_text(combined_raw)
        if not completed or completed == combined_raw:
            return False

        self._replace_visible_text(combined_raw, completed)
        self.committed_context = self._trim_context(self.committed_context + completed)
        self.pending_phrase_raw = ""
        self.raw_token = ""
        if self.latest_suggestions:
            self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
        self._schedule_suggestion_fetch()
        return True

    def _should_use_digit_for_suggestion(self, digit_text: str) -> bool:
        if digit_text not in {"1", "2", "3", "4", "5"} or not self.latest_suggestions:
            return False

        combined_raw = self.pending_phrase_raw + self.raw_token
        if combined_raw and self.engine.would_transform_with_appended_text(combined_raw, digit_text):
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
            self.pending_phrase_raw += self.raw_token + delimiter_visible
            self.raw_token = ""
            if self.latest_suggestions:
                self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
            self._schedule_suggestion_fetch()
            return

        if delimiter_visible.isspace():
            source_visible = combined_raw + delimiter_visible
            replacement_visible = self.engine.finalize_input(combined_raw) + delimiter_visible
        else:
            source_visible = combined_raw + delimiter_visible
            replacement_visible = self.engine.finalize_input(source_visible)

        if replacement_visible != source_visible:
            self._replace_visible_text(source_visible, replacement_visible)
        self.committed_context = self._trim_context(self.committed_context + replacement_visible)
        self.pending_phrase_raw = ""
        self.raw_token = ""
        if self.latest_suggestions:
            self.overlay.show_suggestions(list(self.latest_suggestions), self.active_hwnd)
        self._schedule_suggestion_fetch()

    def _handle_printable_key(self, name: str) -> None:
        self.raw_token += name
        if self._try_auto_complete_current_entry():
            return
        self._schedule_suggestion_fetch()

    def _handle_backspace(self) -> None:
        if self.raw_token:
            self.raw_token = self.raw_token[:-1]
            self._schedule_suggestion_fetch()
            return
        if self.pending_phrase_raw:
            self.pending_phrase_raw = self.pending_phrase_raw[:-1]
            self._schedule_suggestion_fetch()
            return
        if self.committed_context:
            self.committed_context = self.committed_context[:-1]
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
                self.handling_injection = True
                try:
                    import keyboard

                    keyboard.send("backspace")
                finally:
                    self.handling_injection = False

            if combined_raw:
                finalized = self.engine.finalize_input(combined_raw)
                replacement = f"{finalized} {suggestion.word} "
                self._replace_visible_text(combined_raw, replacement)
                self.committed_context = self._trim_context(
                    self.committed_context + replacement
                )
                self.pending_phrase_raw = ""
                self.raw_token = ""
            else:
                needs_space = bool(self.committed_context and not self.committed_context[-1].isspace())
                insertion = f"{' ' if needs_space else ''}{suggestion.word} "
                self.handling_injection = True
                try:
                    import keyboard

                    keyboard.write(insertion, delay=0)
                finally:
                    self.handling_injection = False
                self.committed_context = self._trim_context(self.committed_context + insertion)
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
            self.overlay.show_status("Nufi Windows keyboard OFF")
        else:
            self.overlay.show_status("Nufi Windows keyboard ON")
            self._schedule_suggestion_fetch()

    def _handle_double_shift_toggle(self, event) -> None:
        if event.event_type != "up":
            return
        if not self._is_shift_event(event):
            return
        now = time.monotonic()
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
        for index in range(self.suggestion_limit):
            keyboard.add_hotkey(
                f"ctrl+shift+{index + 1}",
                lambda idx=index: self.select_suggestion(idx),
            )
        self.overlay.set_enabled_state(True)
        self.overlay.show_status("Nufi Windows keyboard ON")

        watcher = threading.Thread(target=self._watch_for_quit, daemon=True)
        watcher.start()
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
    parser = argparse.ArgumentParser(description="Nufi Windows desktop keyboard")
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    app = GlobalNufiWindowsKeyboard(
        api_base_url=args.api_base_url,
        suggestion_limit=args.suggestion_limit,
        suggestion_delay_ms=args.suggestion_delay_ms,
    )
    app.run()
    return 0
