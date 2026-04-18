from pathlib import Path

import nufi_audio as na


def test_load_audio_mapping_parses_csv_file(tmp_path):
    mapping_path = tmp_path / "nufi_word_list.csv"
    mapping_path.write_text(
        "id,raw_row_id,nufi_keyword,audio_file\n"
        "1,1,bà,ba1\n"
        "2,2,mɑ́ kɑ́ lī,makali\n",
        encoding="utf-8",
    )

    na.load_audio_mapping.cache_clear()
    try:
        mapping = na.load_audio_mapping(mapping_path)
    finally:
        na.load_audio_mapping.cache_clear()

    assert mapping == {"bà": "ba1", "mɑ́ kɑ́ lī": "makali"}


def test_load_audio_mapping_can_parse_ts_export_when_explicitly_requested(tmp_path):
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


def test_get_audio_filename_uses_exact_or_low_tone_canonical_match_only():
    mapping = {
        "bà": "ba1",
        "mɑ̀": "maf1",
        "mɑ́ kɑ́ lī": "makali",
        "ntà'sì": "nta1_gsi1",
        "yɑ̀ɑ̀": "yaf11",
    }

    assert na.get_audio_filename("bà", mapping=mapping) == "ba1"
    assert na.get_audio_filename("mɑ", mapping=mapping) == "maf1"
    assert na.get_audio_filename("nta'si", mapping=mapping) == "nta1_gsi1"
    assert na.get_audio_filename("yɑɑ", mapping=mapping) == "yaf11"
    assert na.get_audio_filename("mɑ́ kɑ́ lī", mapping=mapping) == "makali"


def test_get_audio_filename_does_not_fall_back_to_other_tones():
    mapping = {
        "mɑ́": "maf2",
        "mɑ̄": "maf3",
        "ghù": "ghu1",
        "ghʉ̀": "ghuu1",
        "ghʉ̄": "ghuu3",
    }

    assert na.get_audio_filename("mɑ", mapping=mapping) is None
    assert na.get_audio_filename("mǒ'", mapping=mapping) is None
    assert na.get_audio_filename("ghʉ̌", mapping=mapping) is None
    assert na.get_audio_filename("lɑ̌'sǐ", mapping=mapping) is None


def test_audio_mapping_ts_matches_csv_source():
    csv_mapping = na.load_audio_mapping()
    ts_path = Path(__file__).resolve().parents[1] / "audioMapping.ts"
    ts_mapping = na.load_audio_mapping(ts_path)

    assert ts_mapping == csv_mapping


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
