from pathlib import Path
import csv

import nufi_audio as na


def test_load_audio_mapping_parses_ts_export(tmp_path):
    mapping_path = tmp_path / "audioMapping.ts"
    mapping_path.write_text(
        'export const audioMapping: Record<string, string> = {\n'
        '  "bà": "ba1",\n'
        '  "mɑ́ kɑ́ lī": "makali",\n'
        '};\n',
        encoding="utf-8",
    )

    na.load_audio_mapping.cache_clear()
    try:
        mapping = na.load_audio_mapping(mapping_path)
    finally:
        na.load_audio_mapping.cache_clear()

    assert mapping == {"bà": "ba1", "mɑ́ kɑ́ lī": "makali"}


def test_get_audio_filename_finds_exact_and_diacriticless_matches():
    mapping = {
        "bà": "ba1",
        "mɑ́ kɑ́ lī": "makali",
    }

    assert na.get_audio_filename("mɑ́ kɑ́ lī", mapping=mapping) == "makali"
    assert na.get_audio_filename("mɑ kɑ li", mapping=mapping) == "makali"
    assert na.get_audio_filename("bà", mapping=mapping) == "ba1"


def test_get_audio_filename_prefers_low_tone_for_unmarked_words():
    mapping = {
        "mɑ́": "maf2",
        "mɑ̀": "maf1",
        "mɑ̄": "maf3",
        "tɑ́'": "taf2_g",
        "tɑ̀'": "taf1_g",
        "tɑ̄'": "taf3_g",
    }

    assert na.get_audio_filename("mɑ", mapping=mapping) == "maf1"
    assert na.get_audio_filename("tɑ'", mapping=mapping) == "taf1_g"


def test_get_audio_filename_does_not_cross_match_different_vowel_families():
    mapping = {
        "ghù": "ghu1",
        "ghʉ̀": "ghuu1",
        "ghʉ̄": "ghuu3",
    }

    assert na.get_audio_filename("ghʉ̌", mapping=mapping) is None


def test_android_audio_catalog_matches_audio_mapping_ts():
    ts_mapping = na.load_audio_mapping()
    csv_path = (
        Path(__file__).resolve().parents[1]
        / "android-keyboard"
        / "app"
        / "src"
        / "main"
        / "assets"
        / "nufi_word_list.csv"
    )

    csv_mapping = {}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = na.normalize_audio_word((row.get("nufi_keyword") or "").strip())
            value = (row.get("audio_file") or "").strip()
            if key and value:
                csv_mapping[key] = value

    assert csv_mapping == ts_mapping


def test_build_s3_audio_url_quotes_filename():
    url = na.build_s3_audio_url(
        audio_filename="mɑ́_kɑ́_lī",
        bucket_name="dictionnaire-nufi-audio",
        region="us-east-1",
    )

    assert url == (
        "https://dictionnaire-nufi-audio.s3.us-east-1.amazonaws.com/"
        "m%C9%91%CC%81_k%C9%91%CC%81_l%C4%AB.mp3"
    )
