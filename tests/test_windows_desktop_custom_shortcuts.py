from windows_desktop.nufi_windows_keyboard.custom_shortcuts import (
    REMOVAL_SENTINEL,
    load_import_shortcuts,
    parse_shortcuts_text,
)
from windows_desktop.nufi_windows_keyboard.engine import NufiTransformEngine


def test_engine_overlays_custom_exact_shortcuts(tmp_path):
    shortcuts_path = tmp_path / "custom_shortcuts.tsv"
    shortcuts_path.write_text("mbk\tcustom-value\n", encoding="utf-8")

    engine = NufiTransformEngine(custom_shortcuts_path=shortcuts_path)

    assert engine.finalize_input("mbk") == "custom-value"


def test_engine_overlays_custom_phrase_shortcuts(tmp_path):
    shortcuts_path = tmp_path / "custom_shortcuts.tsv"
    shortcuts_path.write_text("af \tcustom-alpha\n", encoding="utf-8")

    engine = NufiTransformEngine(custom_shortcuts_path=shortcuts_path)

    assert engine.finalize_input("af ") == "custom-alpha"


def test_engine_lists_custom_shortcut_hints(tmp_path):
    shortcuts_path = tmp_path / "custom_shortcuts.tsv"
    shortcuts_path.write_text("mzz\tcustom-value\n", encoding="utf-8")

    engine = NufiTransformEngine(custom_shortcuts_path=shortcuts_path)
    hints = engine.get_shortcut_hints("mz", limit=6)

    assert any(hint.shortcut == "mzz" for hint in hints)


def test_load_import_shortcuts_from_csv_with_header(tmp_path):
    shortcuts_path = tmp_path / "import.csv"
    shortcuts_path.write_text("shortcut,replacement\nmbk,custom-value\naf ,custom-alpha\n", encoding="utf-8")

    mappings = load_import_shortcuts(shortcuts_path)

    assert mappings == {"mbk": "custom-value", "af ": "custom-alpha"}


def test_load_import_shortcuts_from_text_with_equals_separator(tmp_path):
    shortcuts_path = tmp_path / "import.txt"
    shortcuts_path.write_text("mbk=custom-value\naff =custom-alpha\n", encoding="utf-8")

    mappings = load_import_shortcuts(shortcuts_path)

    assert mappings == {"mbk": "custom-value", "aff ": "custom-alpha"}


def test_parse_shortcuts_text_supports_removal_lines():
    mappings = parse_shortcuts_text("!mbk\nmzz\tcustom-value\n")

    assert mappings == {"mbk": REMOVAL_SENTINEL, "mzz": "custom-value"}


def test_engine_removes_builtin_exact_shortcuts(tmp_path):
    shortcuts_path = tmp_path / "custom_shortcuts.tsv"
    shortcuts_path.write_text("!mbk\n", encoding="utf-8")

    engine = NufiTransformEngine(custom_shortcuts_path=shortcuts_path)

    assert engine.finalize_input("mbk") == "mbk"
    assert all(hint.shortcut != "mbk" for hint in engine.get_shortcut_hints("mb", limit=10))


def test_load_import_shortcuts_supports_removal_rows(tmp_path):
    shortcuts_path = tmp_path / "import.csv"
    shortcuts_path.write_text("shortcut,replacement\n!mbk,\n", encoding="utf-8")

    mappings = load_import_shortcuts(shortcuts_path)

    assert mappings == {"mbk": REMOVAL_SENTINEL}
