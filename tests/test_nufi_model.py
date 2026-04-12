import nufi_model as nm


def test_clean_text_repairs_mojibake():
    broken = bytes([0x6E, 0x67, 0xC9, 0x91, 0xCC, 0x8C, 0x20, 0x79, 0xC3, 0xBA, 0x27]).decode("latin1")
    assert nm.clean_text(broken) == "ng\u0251\u030c y\u00fa'"


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
