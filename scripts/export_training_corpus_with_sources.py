#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
from pathlib import Path
import sys
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import nufi_model as nm


OUTPUT_PATH = ROOT / "docs" / "training_corpus_unique_sentences_with_sources.txt"
CSV_OUTPUT_PATH = ROOT / "docs" / "training_corpus_unique_sentences_with_sources.csv"
UNIQUE_OUTPUT_PATH = ROOT / "docs" / "training_corpus_unique_sentences_only.txt"
UNIQUE_CSV_OUTPUT_PATH = ROOT / "docs" / "training_corpus_unique_sentences_only.csv"


def _has_unicode_letter(text: str) -> bool:
    return any(unicodedata.category(ch).startswith("L") for ch in text)


def _filter_export_sentence_sources(sentence_sources: dict[str, list[dict]]) -> dict[str, list[dict]]:
    return {
        sentence: entries
        for sentence, entries in sentence_sources.items()
        if sentence and _has_unicode_letter(sentence)
    }


def _sorted_sentences(sentence_sources: dict[str, list[dict]]) -> list[str]:
    return sorted(sentence_sources)


def _sorted_entries(entries: list[dict]) -> list[dict]:
    return sorted(
        entries,
        key=lambda entry: (
            str(entry["path"]),
            str(entry["type"]),
            str(entry["reference"]),
        ),
    )


def _build_source_index(sentence_sources: dict[str, list[dict]]) -> dict[str, int]:
    seen_paths: list[str] = []
    seen_set: set[str] = set()
    for entries in sentence_sources.values():
        for entry in entries:
            path = str(entry["path"])
            if path in seen_set:
                continue
            seen_set.add(path)
            seen_paths.append(path)
    return {path: idx for idx, path in enumerate(sorted(seen_paths), start=1)}


def export_document(output_path: Path = OUTPUT_PATH) -> Path:
    bundle = nm.load_corpus_bundle(str(ROOT))
    sentence_sources = _filter_export_sentence_sources(bundle["sentence_sources"])
    cleaned_sentences = _sorted_sentences(sentence_sources)
    source_index = _build_source_index(sentence_sources)

    source_reference_count = sum(len(entries) for entries in sentence_sources.values())
    source_type_counts = Counter(
        entry["type"]
        for entries in sentence_sources.values()
        for entry in entries
    )

    lines: list[str] = []
    lines.append("NUFI TRAINING CORPUS EXPORT")
    lines.append("==========================")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Workspace: {ROOT}")
    lines.append(f"Unique sentences: {len(cleaned_sentences)}")
    lines.append(f"Unique source files: {len(source_index)}")
    lines.append(f"Sentence-to-source references: {source_reference_count}")
    if source_type_counts:
        lines.append(
            "Source entry types: " + ", ".join(
                f"{kind}={count}" for kind, count in sorted(source_type_counts.items())
            )
        )
    lines.append("")
    lines.append("SOURCE FILES")
    lines.append("------------")
    for path, idx in sorted(source_index.items(), key=lambda item: item[1]):
        lines.append(f"[{idx}] {path}")

    lines.append("")
    lines.append("UNIQUE SENTENCES")
    lines.append("----------------")
    for sentence_number, sentence in enumerate(cleaned_sentences, start=1):
        lines.append("")
        lines.append(f"Sentence {sentence_number}")
        lines.append(sentence)
        lines.append("Sources:")
        for entry in _sorted_entries(sentence_sources.get(sentence, [])):
            source_id = source_index[str(entry['path'])]
            lines.append(
                f"- [{source_id}] {entry['path']} | {entry['type']} | {entry['reference']}"
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return output_path


def export_csv(output_path: Path = CSV_OUTPUT_PATH) -> Path:
    bundle = nm.load_corpus_bundle(str(ROOT))
    sentence_sources = _filter_export_sentence_sources(bundle["sentence_sources"])
    cleaned_sentences = _sorted_sentences(sentence_sources)
    source_index = _build_source_index(sentence_sources)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "sentence_id",
                "sentence",
                "source_id",
                "source_path",
                "source_type",
                "source_reference",
            ],
        )
        writer.writeheader()
        for sentence_id, sentence in enumerate(cleaned_sentences, start=1):
            entries = _sorted_entries(sentence_sources.get(sentence, []))
            if not entries:
                writer.writerow(
                    {
                        "sentence_id": sentence_id,
                        "sentence": sentence,
                        "source_id": "",
                        "source_path": "",
                        "source_type": "",
                        "source_reference": "",
                    }
                )
                continue

            for entry in entries:
                writer.writerow(
                    {
                        "sentence_id": sentence_id,
                        "sentence": sentence,
                        "source_id": source_index[str(entry["path"])],
                        "source_path": entry["path"],
                        "source_type": entry["type"],
                        "source_reference": entry["reference"],
                    }
                )
    return output_path


def export_unique_sentences(output_path: Path = UNIQUE_OUTPUT_PATH) -> Path:
    bundle = nm.load_corpus_bundle(str(ROOT))
    sentence_sources = _filter_export_sentence_sources(bundle["sentence_sources"])
    cleaned_sentences = _sorted_sentences(sentence_sources)

    lines = [
        "NUFI TRAINING CORPUS UNIQUE SENTENCES",
        "===================================",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Workspace: {ROOT}",
        f"Unique sentences: {len(cleaned_sentences)}",
        "",
    ]
    lines.extend(cleaned_sentences)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return output_path


def export_unique_sentences_csv(output_path: Path = UNIQUE_CSV_OUTPUT_PATH) -> Path:
    bundle = nm.load_corpus_bundle(str(ROOT))
    sentence_sources = _filter_export_sentence_sources(bundle["sentence_sources"])
    cleaned_sentences = _sorted_sentences(sentence_sources)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "sentence_id",
                "sentence",
            ],
        )
        writer.writeheader()
        for sentence_id, sentence in enumerate(cleaned_sentences, start=1):
            writer.writerow(
                {
                    "sentence_id": sentence_id,
                    "sentence": sentence,
                }
            )
    return output_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    output_path = export_document()
    csv_output_path = export_csv()
    unique_output_path = export_unique_sentences()
    unique_csv_output_path = export_unique_sentences_csv()
    print(f"Wrote {output_path}")
    print(f"Wrote {csv_output_path}")
    print(f"Wrote {unique_output_path}")
    print(f"Wrote {unique_csv_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
