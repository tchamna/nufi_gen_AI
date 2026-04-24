from windows_desktop.nufi_windows_keyboard.engine import NufiTransformEngine


def test_engine_finalizes_tone_mapping():
    engine = NufiTransformEngine()
    assert engine.finalize_input("ntoho3") == "ntohō"


def test_engine_keeps_embedded_sms_shortcut_out_of_longer_word():
    engine = NufiTransformEngine()
    assert engine.apply_mapping("ntoho3", preserve_ambiguous_trailing_token=True) == "ntoho3"


def test_engine_keeps_standalone_sms_shortcut():
    engine = NufiTransformEngine()
    assert engine.apply_mapping("6*", preserve_ambiguous_trailing_token=True) == "ntohō"
