import keep_only_nufi_v2 as kn2


def test_tokenize_keeps_combining_mark_words_intact():
    assert kn2.tokenize("m\u0251\u0304 o?") == ["m\u0251\u0304", "o", "?"]


def test_segment_text_distinguishes_english_french_and_nufi():
    segmenter = kn2.LanguageSegmenter()
    result = segmenter.segment_text("Hello mon ami, \u01cd c\u00e1' kh\u00f9 \u0101, how are you?")

    assert any(span["language"] == kn2.NUFI for span in result["spans"])
    assert any(span["language"] == kn2.FRENCH for span in result["spans"])
    assert any(span["language"] == kn2.ENGLISH for span in result["spans"])
    assert "\u01cd c\u00e1' kh\u00f9 \u0101," in result["grouped"][kn2.NUFI]


def test_keep_only_nufi_text_extracts_nufi_span():
    segmenter = kn2.LanguageSegmenter()
    text = "Bonjour, \u01cd c\u00e1' kh\u00f9 \u0101, hello there."

    assert segmenter.keep_only_nufi_text(text) == "\u01cd c\u00e1' khu \u0101,"


def test_protected_ambiguous_tokens_are_nufi():
    segmenter = kn2.LanguageSegmenter()

    for token in ["o", "a", "pen", "po", "tua", "n", "soh"]:
        assert segmenter.classify_token(token, kn2.normalize_token(token)) == kn2.NUFI

    assert segmenter.classify_token("fa'á", kn2.normalize_token("fa'á")) == kn2.NUFI


def test_shared_english_french_words_get_shared_label():
    segmenter = kn2.LanguageSegmenter()

    assert segmenter.classify_token("test", kn2.normalize_token("test")) == kn2.ENGLISH_FRENCH


def test_accented_french_words_do_not_fall_back_to_nufi():
    segmenter = kn2.LanguageSegmenter()

    assert segmenter.classify_token("personnifiés", kn2.normalize_token("personnifiés")) == kn2.FRENCH
    assert segmenter.classify_token("aèdes", kn2.normalize_token("aèdes")) == kn2.FRENCH
    assert segmenter.classify_token("l'hyène", kn2.normalize_token("l'hyène")) == kn2.FRENCH
    assert segmenter.classify_token("l'enjamba", kn2.normalize_token("l'enjamba")) == kn2.FRENCH
    assert segmenter.classify_token("tordirent", kn2.normalize_token("tordirent")) == kn2.FRENCH


def test_french_conjugated_and_derived_forms_are_detected():
    segmenter = kn2.LanguageSegmenter()

    for word in ["boitait", "fuirent", "creusa", "va", "ruminent", "tuions", "puiserai", "supporteras", "poltronne"]:
        assert segmenter.classify_token(word, kn2.normalize_token(word)) == kn2.FRENCH


def test_cleanup_preserves_standalone_a_and_collapses_repeated_words():
    assert kn2.cleanup_nufi_output("a") == "a"
    assert kn2.cleanup_nufi_output("a a") == "a"
    assert kn2.cleanup_nufi_output("foo a a bar") == "foo a bar"
    assert kn2.cleanup_nufi_output("Si Si si") == "Si"


def test_keep_only_nufi_text_preserves_short_tonal_tokens():
    segmenter = kn2.LanguageSegmenter()

    assert segmenter.keep_only_nufi_text("Lǎh nzhì ò ncáh mbú à") == "Lǎh nzhi o ncáh mbú a"
    assert segmenter.keep_only_nufi_text("Tēh hèé ná mbát ncáh mbú à") == "Tēh heé ná mbát ncáh mbú a"
    assert segmenter.keep_only_nufi_text("Lǎh soh ntēh mbī' lɑ́ nɑ́ ndhī o") == "Lǎh soh ntēh mbī' lɑ́ nɑ́ ndhī o"


def test_unknown_titlecase_names_are_other():
    segmenter = kn2.LanguageSegmenter()

    assert segmenter.classify_token("Tchamda", kn2.normalize_token("Tchamda")) == kn2.OTHER
    assert segmenter.classify_token("Nupo", kn2.normalize_token("Nupo")) == kn2.OTHER


def test_unknown_bare_vowel_word_assumes_ton_bas_and_is_nufi():
    segmenter = kn2.LanguageSegmenter()

    assert kn2.assume_low_tone_word("nhee") == "nhèè"
    assert segmenter.classify_token("nhee", kn2.normalize_token("nhee")) == kn2.NUFI


def test_user_examples_are_classified_as_nufi_sentences():
    segmenter = kn2.LanguageSegmenter()
    examples = [
        "Póómɑ̄, n shʉɑ́ pen sī’ ntóó nkɑ̄ɑ̄ ba, ntóó nhee mǎ,",
        "ntóó mbe’e mǎ, tɑ́’, sī mfɑ’ mǎ bɑ̄ !",
        "Zhī’sī ghəə zǒ, mbɑ̄ yǒ wenok.",
        "O sǐ’ nzhī ghəə zǒ bɑ̄, mɑ pó mfén ō pu’.",
    ]

    for text in examples:
        result = segmenter.segment_text(text)
        labels = [token["label"] for token in result["tokens"] if token["label"] != kn2.PUNCT]
        assert labels
        assert set(labels) == {kn2.NUFI}
