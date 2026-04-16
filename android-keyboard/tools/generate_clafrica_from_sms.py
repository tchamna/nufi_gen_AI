from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = ROOT / "nufi_sms_and_calendar.xlsx"
OUTPUT_PATH = ROOT / "app" / "src" / "main" / "assets" / "clafrica.json"
SHEET_NAME = "Nufi_SMS"


def main() -> None:
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

    OUTPUT_PATH.write_text(
        json.dumps(mapping, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    duplicate_keys = {key: rows for key, rows in duplicates.items() if len(rows) > 1}
    print(
        f"Wrote {len(mapping)} shortcuts from {usable_rows} rows in "
        f"{WORKBOOK_PATH.name}:{SHEET_NAME} to {OUTPUT_PATH}"
    )
    if duplicate_keys:
        print("Duplicate shortcuts resolved by keeping the last row:")
        for key in sorted(duplicate_keys):
            print(f"  {key} -> rows {duplicate_keys[key]}")


if __name__ == "__main__":
    main()
