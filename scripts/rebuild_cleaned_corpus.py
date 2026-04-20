#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import argparse
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET
import runpy


ROOT = Path(__file__).resolve().parents[1]
CLEANED_ROOT = ROOT / "cleaned"
LEGACY_WORKSPACE_CLEANED_FILES = {
    "corpus_vocabulaire_nufi_test.txt": CLEANED_ROOT / "corpus_vocabulaire_nufi_test.clean.txt",
}
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import keep_only_nufi_v2 as kn

EXTERNAL_NUFI_DOCUMENTS_DIR = Path(r"G:\My Drive\Data_Science\DataSets\Nufi\Nufi_Documents")
EXTERNAL_SOURCE_DIRS = [
    EXTERNAL_NUFI_DOCUMENTS_DIR / "Nufi_Only",
    EXTERNAL_NUFI_DOCUMENTS_DIR / "Nufi_Francais",
]
WORKSPACE_CORPUS_FILES = [
    ROOT / "corpus_vocabulaire_nufi_test.txt",
]
GENERATED_OUTPUT_FILES = {
    "main_file1": ROOT / "main_file1.txt",
    "main_file2": ROOT / "main_file2.txt",
    "main_file": ROOT / "main_file.txt",
    "corpus_vocabulaire": ROOT / "corpus_vocabulaire_nufi_test.txt",
}
# Provenance line to include in generated outputs (kept verbatim)
SOURCE_LINE = "(Source: From Shck Tchamna Nufi Dictionary)"
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def extract_docx_text(path: Path) -> str:
    with ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    paragraphs = []
    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        chunks = []
        for node in paragraph.findall(".//w:t", WORD_NAMESPACE):
            if node.text:
                chunks.append(node.text)
        if chunks:
            paragraphs.append("".join(chunks))
    return "\n".join(paragraphs)


def iter_external_source_files() -> list[tuple[Path, Path]]:
    files = []
    for source_dir in EXTERNAL_SOURCE_DIRS:
        if not source_dir.exists():
            continue
        for suffix in ("*.docx", "*.txt", "*.srt"):
            for path in source_dir.rglob(suffix):
                if path.name.startswith("~$"):
                    continue
                files.append((source_dir, path))
    return sorted(files)


def clean_text(text: str, segmenter: kn.LanguageSegmenter) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        cleaned = segmenter.keep_only_nufi_text(raw_line.rstrip("\n"))
        cleaned = cleaned.strip()
        if cleaned:
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def read_source_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            return extract_docx_text(path)
        except BadZipFile:
            return path.read_text(encoding="utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = "\n" if content and not content.endswith("\n") else ""
    path.write_text(content + suffix, encoding="utf-8-sig")


def rebuild(generate_visuals: bool = True) -> int:
    segmenter = kn.LanguageSegmenter()

    external_files = iter_external_source_files()
    if not external_files:
        print(f"External corpus folders not found or empty: {EXTERNAL_SOURCE_DIRS}")

    cleaned_docx_outputs = []
    cleaned_txt_outputs = []

    for source_root, source in external_files:
        raw_text = read_source_text(source)
        cleaned = clean_text(raw_text, segmenter)
        destination = CLEANED_ROOT / "external" / source_root.name / source.relative_to(source_root).with_suffix(".clean.txt")
        write_text(destination, cleaned)
        if source.suffix.lower() == ".docx":
            cleaned_docx_outputs.append(destination)
        else:
            cleaned_txt_outputs.append(destination)
        print(f"Wrote cleaned file: {destination}")

    for source in WORKSPACE_CORPUS_FILES:
        if not source.exists():
            continue
        raw_text = read_source_text(source)
        cleaned = clean_text(raw_text, segmenter)
        destination = CLEANED_ROOT / "workspace" / source.name.replace(".txt", ".clean.txt")
        write_text(destination, cleaned)
        legacy_destination = LEGACY_WORKSPACE_CLEANED_FILES.get(source.name)
        if legacy_destination is not None:
            write_text(legacy_destination, cleaned)
        if source.name == "corpus_vocabulaire_nufi_test.txt":
            write_text(GENERATED_OUTPUT_FILES["corpus_vocabulaire"], cleaned)
        print(f"Wrote cleaned workspace file: {destination}")

    main_file1 = "\n\n".join(path.read_text(encoding="utf-8-sig") for path in cleaned_docx_outputs if path.exists()).strip()
    main_file2 = "\n\n".join(path.read_text(encoding="utf-8-sig") for path in cleaned_txt_outputs if path.exists()).strip()
    main_file = "\n\n".join(part for part in (main_file1, main_file2) if part).strip()

    write_text(CLEANED_ROOT / "main_file1.clean.txt", main_file1)
    write_text(CLEANED_ROOT / "main_file2.clean.txt", main_file2)
    write_text(CLEANED_ROOT / "main_file.clean.txt", main_file)

    # Create a deduplicated (order-preserving) version of the combined main file
    def _dedupe_preserve_order(text: str) -> str:
        if not text:
            return ""
        seen = set()
        out_lines = []
        for ln in text.splitlines():
            line = ln.rstrip("\n\r")
            if not line:
                continue
            if line in seen:
                continue
            seen.add(line)
            out_lines.append(line)
        return "\n".join(out_lines)

    unique_main = _dedupe_preserve_order(main_file)
    write_text(CLEANED_ROOT / "main_file.unique.clean.txt", unique_main)
    write_text(ROOT / "main_file.unique.txt", SOURCE_LINE + "\n\n" + unique_main if unique_main else "")

    def _maybe_prepend_source(content: str) -> str:
        if not content:
            return content
        return SOURCE_LINE + "\n\n" + content

    write_text(GENERATED_OUTPUT_FILES["main_file1"], _maybe_prepend_source(main_file1))
    write_text(GENERATED_OUTPUT_FILES["main_file2"], _maybe_prepend_source(main_file2))
    write_text(GENERATED_OUTPUT_FILES["main_file"], _maybe_prepend_source(main_file))

    print(f"Rebuilt {GENERATED_OUTPUT_FILES['main_file1']}")
    print(f"Rebuilt {GENERATED_OUTPUT_FILES['main_file2']}")
    print(f"Rebuilt {GENERATED_OUTPUT_FILES['main_file']}")
    print(f"Refreshed {GENERATED_OUTPUT_FILES['corpus_vocabulaire']}")
    if generate_visuals:
        # Generate visualization artifacts (wordcloud + bar chart)
        try:
            print('Generating visual artifacts (wordcloud, bar chart)')
            scripts_dir = ROOT / 'scripts'
            wc_script = scripts_dir / 'generate_real_wordcloud.py'
            bar_script = scripts_dir / 'generate_top_bar_chart.py'
            if wc_script.exists():
                runpy.run_path(str(wc_script), run_name='__main__')
            else:
                print('Wordcloud script not found:', wc_script)
            if bar_script.exists():
                runpy.run_path(str(bar_script), run_name='__main__')
            else:
                print('Bar chart script not found:', bar_script)
            print('Visual artifacts generation completed')
        except Exception as exc:
            print('Visual generation skipped/failed:', type(exc).__name__, exc)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild cleaned corpus and generated outputs.")
    parser.add_argument('--no-visuals', action='store_true', help='Skip generating visual artifacts (wordcloud, charts)')
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(rebuild(generate_visuals=not args.no_visuals))
