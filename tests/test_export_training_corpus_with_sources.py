from pathlib import Path

from scripts import export_training_corpus_with_sources as exports


def test_filter_export_sentence_sources_drops_non_alpha_sentences():
    sentence_sources = {
        "1": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
        "001 --> 002": [{"path": "a.txt", "type": "txt", "reference": "line 2"}],
        "01 03 666 --> 01 06 102": [{"path": "a.txt", "type": "txt", "reference": "line 3"}],
        "mɑ́ kɑ́ lī": [{"path": "b.txt", "type": "txt", "reference": "line 4"}],
        "ntúmbō 1964": [{"path": "c.txt", "type": "txt", "reference": "line 5"}],
    }

    filtered = exports._filter_export_sentence_sources(sentence_sources)

    assert "1" not in filtered
    assert "001 --> 002" not in filtered
    assert "01 03 666 --> 01 06 102" not in filtered
    assert "mɑ́ kɑ́ lī" in filtered
    assert "ntúmbō 1964" in filtered


def test_export_unique_sentences_omits_numeric_only_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(
        exports.nm,
        "load_corpus_bundle",
        lambda base_dir: {
            "cleaned": [],
            "tokens": [],
            "sentence_sources": {
                "1": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
                "001 --> 002": [{"path": "a.txt", "type": "txt", "reference": "line 2"}],
                "mɑ́ kɑ́ lī": [{"path": "b.txt", "type": "txt", "reference": "line 3"}],
            },
        },
    )

    output_path = tmp_path / "training_corpus_unique_sentences_only.txt"
    exports.export_unique_sentences(output_path)
    text = output_path.read_text(encoding="utf-8-sig")

    assert "mɑ́ kɑ́ lī" in text
    assert "001 --> 002" not in text
