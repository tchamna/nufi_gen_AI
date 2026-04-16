from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
WORKBOOK_PATH = ROOT / "nufi_sms_and_calendar.xlsx"
BASE_MAPPING_PATH = REPO_ROOT / "clafricaMapping.ts"
ASSETS_DIR = ROOT / "app" / "src" / "main" / "assets"
CLAFRICA_OUTPUT_PATH = ASSETS_DIR / "clafrica.json"
SMS_OUTPUT_PATH = ASSETS_DIR / "nufi_sms.json"
SHEET_NAME = "Nufi_SMS"


def load_base_mapping() -> dict[str, str]:
    if BASE_MAPPING_PATH.exists():
        result = subprocess.run(
            [
                "npx.cmd",
                "tsx",
                "-e",
                (
                    "import { Clafrica } from './clafricaMapping.ts'; "
                    "process.stdout.write(JSON.stringify(Clafrica));"
                ),
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Failed to load base Clafrica map: {stderr}")
        return json.loads(result.stdout.decode("utf-8"))

    raise FileNotFoundError(
        f"Could not find base mapping source {BASE_MAPPING_PATH}"
    )


def load_sms_mapping() -> tuple[dict[str, str], dict[str, list[int]], int]:
    workbook = load_workbook(WORKBOOK_PATH, data_only=True)
    sheet = workbook[SHEET_NAME]

    mapping: dict[str, str] = {}
    duplicates: dict[str, list[int]] = defaultdict(list)
    usable_rows = 0

    for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        shortcut = "" if row[1] is None else str(row[1]).strip()
        replacement = "" if row[2] is None else str(row[2]).strip()
        if not shortcut or not replacement:
            continue

        usable_rows += 1
        if shortcut in mapping:
            duplicates[shortcut].append(row_number)
        else:
            duplicates[shortcut] = [row_number]
        mapping[shortcut] = replacement

    duplicate_keys = {key: rows for key, rows in duplicates.items() if len(rows) > 1}
    return mapping, duplicate_keys, usable_rows


def main() -> None:
    base_mapping = load_base_mapping()
    sms_mapping, duplicate_keys, usable_rows = load_sms_mapping()
    overlap = sorted(set(base_mapping) & set(sms_mapping))
    CLAFRICA_OUTPUT_PATH.write_text(
        json.dumps(base_mapping, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    SMS_OUTPUT_PATH.write_text(
        json.dumps(sms_mapping, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(
        f"Wrote {len(base_mapping)} base shortcuts to {CLAFRICA_OUTPUT_PATH.name}"
    )
    print(f"Wrote {len(sms_mapping)} SMS shortcuts to {SMS_OUTPUT_PATH.name}")
    print(f"SMS usable rows: {usable_rows}")
    print(f"Overlapping keys overridden by SMS: {len(overlap)}")
    if duplicate_keys:
        print("Duplicate shortcuts resolved by keeping the last row:")
        for key in sorted(duplicate_keys):
            print(f"  {key} -> rows {duplicate_keys[key]}")


if __name__ == "__main__":
    main()
