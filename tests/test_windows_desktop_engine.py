from windows_desktop.nufi_windows_keyboard.engine import NufiTransformEngine


FORMER_DOLLAR_SHORTCUTS = {
    "mb'": "mbe'",
    "mbk": "mbak",
    "mbl": "mbə̄ə̄ lɑ́",
    "ndnd": "ndéndēē",
    "ngkw'": "ngɑ̌ kwa'",
    "ppl": "pen pə̄ə̄ lɑ́",
    "ss": "sī sīē",
}


def test_engine_finalizes_tone_mapping():
    engine = NufiTransformEngine()
    assert engine.finalize_input("ntoho3") == "ntohō"


def test_engine_keeps_embedded_sms_shortcut_out_of_longer_word():
    engine = NufiTransformEngine()
    assert engine.apply_mapping("ntoho3", preserve_ambiguous_trailing_token=True) == "ntoho3"


def test_engine_keeps_standalone_sms_shortcut():
    engine = NufiTransformEngine()
    assert engine.apply_mapping("6*", preserve_ambiguous_trailing_token=True) == "ntohō"


def test_engine_finalizes_ambiguous_sms_shortcut_exact_match():
    engine = NufiTransformEngine()
    assert engine.finalize_input("ppl") == "pen pə̄ə̄ lɑ́"


def test_engine_finalizes_longer_sms_shortcut_with_same_prefix():
    engine = NufiTransformEngine()
    assert engine.finalize_input("pplpmo") == "pen pə̄ə̄ lɑ́ poómɑ̄ ō"


def test_engine_keeps_ambiguous_exact_shortcut_literal_while_typing():
    engine = NufiTransformEngine()
    assert engine.auto_complete_exact_text("ppl") is None
    assert engine.apply_mapping("ppl", preserve_ambiguous_trailing_token=True) == "ppl"


def test_engine_keeps_other_ambiguous_exact_shortcut_literal_while_typing():
    engine = NufiTransformEngine()
    assert engine.apply_mapping("mbk", preserve_ambiguous_trailing_token=True) == "mbk"


def test_engine_finalizes_former_dollar_shortcuts_without_dollar_suffix():
    engine = NufiTransformEngine()
    for shortcut, expected in FORMER_DOLLAR_SHORTCUTS.items():
        assert engine.finalize_input(shortcut) == expected


def test_engine_lists_shortcut_hints_for_prefix():
    engine = NufiTransformEngine()
    hints = engine.get_shortcut_hints("mb", limit=6)
    suffixes = {hint.remaining for hint in hints}
    assert "'" in suffixes
    assert "k" in suffixes
    assert "l" in suffixes


def test_engine_shortcut_hints_shrink_as_prefix_grows():
    engine = NufiTransformEngine()
    hints = engine.get_shortcut_hints("mbl", limit=6)
    assert hints == []


def test_engine_does_not_expand_embedded_sms_alias_inside_longer_token():
    engine = NufiTransformEngine()
    assert engine.finalize_input("nkaff3") == "nkɑ̄ɑ̄"


def test_engine_finalizes_plain_vowel_space_shortcuts():
    engine = NufiTransformEngine()
    assert engine.finalize_input("af ") == "ɑ"
    assert engine.finalize_input("aff ") == "ɑ"
    assert engine.finalize_input("eu ") == "ə"
    assert engine.finalize_input("ai ") == "ε"
    assert engine.finalize_input("uu ") == "ʉ"
    assert engine.finalize_input("uuaf ") == "ʉɑ"


def test_engine_applies_uu_inside_longer_word():
    engine = NufiTransformEngine()
    assert engine.finalize_input("ntuu") == "ntʉ"
