import nufi_model as nm


def test_clean_text_repairs_mojibake():
    broken = bytes([0x6E, 0x67, 0xC9, 0x91, 0xCC, 0x8C, 0x20, 0x79, 0xC3, 0xBA, 0x27]).decode("latin1")
    assert nm.clean_text(broken) == "ng\u0251\u030c y\u00fa'"


def test_clean_text_strips_low_tone_with_ton_bas():
    assert nm.clean_text("s\u00ec") == "si"  # sì → si (dict_ton_bas)


def test_clean_text_unifies_modifier_apostrophe_for_bana():
    # U+02BC must become ASCII ' so hə̌' → hě' (schwa map matches)
    w = "h\u0259\u030c\u02bcnz\u012b"
    assert nm.clean_text(w) == "h\u011b'nz\u012b"


def test_suggest_next_words_bare_vowel_equivalent_to_low_tone():
    # Model only has "pèn" in context; user types "pen" (no accent) → same lookup as pèn
    tokens = [["p\u00e8n", "after"]]
    model = nm.build_combined_model(tokens, max_n=3)
    payload = nm.suggest_next_words(model, "pen", n=2, limit=5)
    words = [s["word"] for s in payload["suggestions"]]
    assert "after" in words


def test_suggest_next_words_falls_back_when_model_uses_legacy_tone_marks():
    # Model key is still "pèn"; full clean_text maps input to "pen" — fallback finds context.
    tokens = [["p\u00e8n", "next"]]
    model = nm.build_combined_model(tokens, max_n=3)
    payload = nm.suggest_next_words(model, "p\u00e8n", n=2, limit=5)
    words = [s["word"] for s in payload["suggestions"]]
    assert "next" in words


def test_suggest_next_words_normalizes_display_words():
    # Model stores legacy token "sì"; display must still use ton_bas → "si"
    tokens = [["hello", "s\u00ec"]]
    model = nm.build_combined_model(tokens, max_n=3)
    payload = nm.suggest_next_words(model, "hello", n=2, limit=5)
    words = [s["word"] for s in payload["suggestions"]]
    assert "si" in words
    assert "\u00ec" not in "".join(words)


def test_suggest_next_words_dedupes_colliding_display_forms():
    # Two distinct model keys that clean_text maps to the same word (common with legacy pickles).
    model = {
        ("hello",): {"lah": 0.25, "l\u00e0h": 0.25, "other": 0.1},
    }
    payload = nm.suggest_next_words(model, "hello", n=2, limit=8)
    words = [s["word"] for s in payload["suggestions"]]
    assert words.count("lah") == 1
    lah = next(s for s in payload["suggestions"] if s["word"] == "lah")
    assert abs(lah["probability"] - 0.5) < 1e-9


def test_strip_nota_bene_removes_n_space_b_token_pair():
    # "n. b." → after clean_text becomes "n b" (spurious bigram); stripping removes the marker.
    raw = "foo n. b. bar"
    stripped = nm._strip_nota_bene_markers(raw)
    assert nm.clean_text(stripped).split() == ["foo", "bar"]


def test_strip_nota_bene_handles_nb_without_space():
    # "n.b." → clean_text is one token "nb", not n then b; strip still removes editor note.
    raw = "demi n.b. tail"
    stripped = nm._strip_nota_bene_markers(raw)
    assert nm.clean_text(stripped).split() == ["demi", "tail"]


def test_suggest_next_words_drops_singleton_n_to_b_artifact():
    # Legacy / unrebuilt pickles: only ("n",)->b from Latin "N. B." tokenization.
    model = {("n",): {"b": 1.0}}
    payload = nm.suggest_next_words(model, "n", n=2, limit=5)
    assert payload["suggestions"] == []


def test_suggest_next_words_keeps_b_after_n_when_other_continuations_exist():
    model = {("n",): {"b": 0.5, "lah": 0.5}}
    payload = nm.suggest_next_words(model, "n", n=2, limit=5)
    words = [s["word"] for s in payload["suggestions"]]
    assert "b" in words and "lah" in words


def test_find_corpus_matches_prioritizes_exact_match():
    corpus = [
        "ng\u0251\u030c y\u00fa'",
        "ng\u0251\u030c y\u00fa' m\u0251\u0301 \u00e1 y\u01cet",
        "other sentence",
    ]
    matches = nm.find_corpus_matches(corpus, "ng\u0251\u030c y\u00fa'", limit=5)
    assert matches[0] == "ng\u0251\u030c y\u00fa'"
    assert matches[1] == "ng\u0251\u030c y\u00fa' m\u0251\u0301 \u00e1 y\u01cet"


def test_generate_candidates_returns_original_status_for_known_sentence():
    tokens = [
        ["hello", "world"],
        ["hello", "there"],
    ]
    model = nm.build_combined_model(tokens, max_n=3)
    known = {"hello world", "hello there"}

    normalized_text, candidates = nm.generate_candidates(
        model,
        "hello",
        n=3,
        known_sentences=known,
        max_tokens=3,
        temperature=0,
        num_candidates=3,
    )

    assert normalized_text == "hello"
    assert candidates
    assert candidates[0]["status"] == "original"
    assert candidates[0]["result"] in known


def test_generate_text_details_reports_not_in_corpus():
    tokens = [["hello", "world"]]
    model = nm.build_combined_model(tokens, max_n=3)

    result = nm.generate_text_details(model, "missing phrase", n=3)

    assert result["status"] == "not_in_corpus"
    assert result["result"].endswith("not in corpus")


def test_read_records_from_srt_strips_indices_and_timestamps(tmp_path):
    srt_file = tmp_path / "sample.srt"
    srt_file.write_text(
        "1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n2\n00:00:05,000 --> 00:00:06,000\nSecond line\n",
        encoding="utf-8",
    )

    records = nm._read_records_from_srt(srt_file)

    assert [record["text"] for record in records] == ["Hello world", "Second line"]
    assert records[0]["reference"] == "subtitle 1"


def test_load_directory_records_recurses_into_subfolders(tmp_path):
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)

    (root / "top.txt").write_text("top line\n", encoding="utf-8")
    (nested / "sub.srt").write_text(
        "1\n00:00:01,000 --> 00:00:02,000\nnested line\n",
        encoding="utf-8",
    )

    records = nm._load_directory_records(root)
    texts = [record["text"] for record in records]

    assert "top line\n" in texts
    assert "nested line" in texts


def test_load_corpus_bundle_preserves_sentence_sources(tmp_path):
    (tmp_path / "corpus_vocabulaire_nufi_test.txt").write_text("Hello world\nHello world\n", encoding="utf-8")
    data_dir = tmp_path / "data" / "Nufi"
    data_dir.mkdir(parents=True)
    (data_dir / "phrasebooknufi.txt").write_text("Another line\n", encoding="utf-8")

    original_external = nm.EXTERNAL_NUFI_ONLY_DIR
    nm.EXTERNAL_NUFI_ONLY_DIR = str(tmp_path / "missing")
    try:
        bundle = nm.load_corpus_bundle(tmp_path)
    finally:
        nm.EXTERNAL_NUFI_ONLY_DIR = original_external

    assert "hello world" in bundle["cleaned"]
    assert "another line" in bundle["cleaned"]
    assert bundle["sentence_sources"]["hello world"][0]["reference"] == "line 1"


def test_suggest_next_words_prefers_nufi_orthography_on_probability_ties():
    # Equal counts → equal p; ō (U+014D) should rank before bare o
    tokens = [["p\u00f3\u00f3m\u0251\u0304", "\u014d"], ["p\u00f3\u00f3m\u0251\u0304", "o"]]
    model = nm.build_combined_model(tokens, max_n=3)
    payload = nm.suggest_next_words(model, "p\u00f3\u00f3m\u0251\u0304", n=2, limit=5)
    words = [s["word"] for s in payload["suggestions"]]
    assert words[0] == "\u014d"  # ō


def test_is_punctuation_only_token():
    assert nm._is_punctuation_only_token("...") is True
    assert nm._is_punctuation_only_token("\u00bb") is True  # »
    assert nm._is_punctuation_only_token('"') is True
    assert nm._is_punctuation_only_token("m\u00e1") is False


def test_suggest_next_words_skips_punctuation_only_tokens():
    model = {
        ("seed",): {"word": 0.3, "...": 0.25, "\u00bb": 0.25, "ok": 0.2},
    }
    payload = nm.suggest_next_words(model, "seed", n=2, limit=8)
    words = [s["word"] for s in payload["suggestions"]]
    assert "word" in words
    assert "ok" in words
    assert "..." not in words
    assert "\u00bb" not in words


def test_suggest_next_words_returns_ranked_words():
    tokens = [
        ["hello", "world"],
        ["hello", "there"],
        ["hello", "world"],
    ]
    model = nm.build_combined_model(tokens, max_n=3)

    payload = nm.suggest_next_words(model, "hello", n=3, limit=3)

    assert payload["normalized_text"] == "hello"
    assert payload["suggestions"][0]["word"] == "world"
    assert payload["used_context"] >= 1


def test_exclude_french_meta_line():
    raw = "Ce qui correspond à l'expression française suivante"
    assert nm._exclude_sentence_for_nufi_only(raw, nm.clean_text(raw)) is True


def test_keep_nufi_line_with_ipa():
    raw = "\u00c0 b\u0251\u0301 hello"
    assert nm._exclude_sentence_for_nufi_only(raw, nm.clean_text(raw)) is False


def test_load_corpus_bundle_skips_french_meta(tmp_path):
    (tmp_path / "corpus_vocabulaire_nufi_test.txt").write_text(
        "Ce qui correspond à l'expression française suivante\n"
        "\u00c0 b\u0251\u0301 hello\n",
        encoding="utf-8",
    )
    original_external = nm.EXTERNAL_NUFI_ONLY_DIR
    nm.EXTERNAL_NUFI_ONLY_DIR = str(tmp_path / "missing")
    try:
        bundle = nm.load_corpus_bundle(tmp_path)
    finally:
        nm.EXTERNAL_NUFI_ONLY_DIR = original_external

    joined = " ".join(bundle["cleaned"])
    assert "ce qui correspond" not in joined
    assert "hello" in joined
