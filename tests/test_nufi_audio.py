from pathlib import Path

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
