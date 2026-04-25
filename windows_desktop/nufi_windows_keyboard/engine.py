from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class DynamicDateAlias:
    offset_days: int
    intro: str | None = None


@dataclass(frozen=True)
class ShortcutHint:
    prefix: str
    shortcut: str
    remaining: str


class NufiTransformEngine:
    def __init__(self, asset_root: Path | None = None) -> None:
        if asset_root is None:
            if getattr(sys, "_MEIPASS", None):
                asset_root = (
                    Path(sys._MEIPASS)
                    / "android-keyboard"
                    / "app"
                    / "src"
                    / "main"
                    / "assets"
                )
            else:
                asset_root = (
                    Path(__file__).resolve().parents[2]
                    / "android-keyboard"
                    / "app"
                    / "src"
                    / "main"
                    / "assets"
                )
        self.asset_root = asset_root
        self.default_calendar_intro = "Zě'é mɑ́"
        self.dynamic_date_aliases = {
            "today*": DynamicDateAlias(0),
            "aujourd'hui*": DynamicDateAlias(0),
            "aujourdhui*": DynamicDateAlias(0),
            "date*": DynamicDateAlias(0),
            "l'nz": DynamicDateAlias(0),
            "ze'e*": DynamicDateAlias(0),
            "now*": DynamicDateAlias(0),
            "yesterday*": DynamicDateAlias(-1, "Wāha kɑ̌'"),
            "*waha": DynamicDateAlias(-1, "Wāha kɑ̌'"),
            "tomorrow*": DynamicDateAlias(1, "Wāhá imbɑ̄"),
            "waha*": DynamicDateAlias(1, "Wāhá imbɑ̄"),
        }
        self.calendar_pattern = re.compile(r"(?<![\w])(\d{1,2})([ -])(\d{1,2})\2(\d{4})(?![\w])")

        self.clafrica_token_map: dict[str, str] = {}
        self.exact_token_map: dict[str, str] = {}
        self.phrase_map: dict[str, str] = {}
        self.calendar_map: dict[str, str] = {}

        self._load_assets()
        self.compositional_keys_sorted = sorted(
            self.clafrica_token_map.keys(),
            key=lambda item: (-len(item), item),
        )
        self.exact_keys_sorted = sorted(
            self.exact_token_map.keys(),
            key=lambda item: (-len(item), item),
        )
        self.phrase_patterns_sorted = [
            (re.compile(rf"(?<![\w]){re.escape(key)}(?![\w])"), value)
            for key, value in sorted(
                self.phrase_map.items(),
                key=lambda item: (-len(item[0]), item[0]),
            )
        ]
        self.ambiguous_keys = {
            key
            for key in self.exact_keys_sorted
            if any(len(other) > len(key) and other.startswith(key) for other in self.exact_keys_sorted)
        }
        self.ambiguous_phrase_keys = {
            key
            for key in self.phrase_map.keys()
            if any(len(other) > len(key) and other.startswith(key) for other in self.phrase_map.keys())
        }
        all_shortcut_keys = {
            *(self.exact_token_map.keys()),
            *(self.phrase_map.keys()),
            *(self.dynamic_date_aliases.keys()),
        }
        self.shortcut_keys_sorted = sorted(
            (
                key
                for key in all_shortcut_keys
                if not (key.endswith("?") and key[:-1] in all_shortcut_keys)
            ),
            key=lambda item: (len(item), item.lower(), item),
        )

    def _load_json_asset(self, name: str) -> dict[str, str]:
        with (self.asset_root / name).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _load_asset_map(
        self,
        asset_name: str,
        token_destination: dict[str, str],
        phrase_destination: dict[str, str],
    ) -> None:
        for key, value in self._load_json_asset(asset_name).items():
            if any(ch.isspace() for ch in key):
                phrase_destination[key] = value
            else:
                token_destination[key] = value

    def _load_assets(self) -> None:
        clafrica_tokens: dict[str, str] = {}
        sms_tokens: dict[str, str] = {}
        phrases: dict[str, str] = {}
        self._load_asset_map("clafrica.json", clafrica_tokens, phrases)
        self._load_asset_map("nufi_sms.json", sms_tokens, phrases)
        clafrica_tokens["uu"] = "ʉ"
        self.clafrica_token_map = clafrica_tokens
        self.exact_token_map = dict(clafrica_tokens)
        self.exact_token_map.update(sms_tokens)
        self.phrase_map = phrases
        self.phrase_map.update(
            {
                "af ": "ɑ",
                "aff ": "ɑ",
                "eu ": "ə",
                "ai ": "ε",
                "uu ": "ʉ",
                "uuaf ": "ʉɑ",
            }
        )
        self._add_optional_question_aliases()
        self.calendar_map = self._load_json_asset("nufi_calendar.json")

    def _add_optional_question_aliases(self) -> None:
        token_aliases: dict[str, str] = {}
        for key, value in self.exact_token_map.items():
            if not key.endswith("?"):
                continue
            alias = key[:-1]
            if alias and alias not in self.exact_token_map:
                token_aliases[alias] = value
        self.exact_token_map.update(token_aliases)

        phrase_aliases: dict[str, str] = {}
        for key, value in self.phrase_map.items():
            if not key.endswith("?"):
                continue
            alias = key[:-1]
            if alias and alias not in self.phrase_map:
                phrase_aliases[alias] = value
        self.phrase_map.update(phrase_aliases)

    @staticmethod
    def _split_with_whitespace(text: str) -> list[str]:
        if not text:
            return [""]
        out: list[str] = []
        index = 0
        for match in re.finditer(r"(\s+)", text):
            if match.start() > index:
                out.append(text[index:match.start()])
            out.append(match.group(0))
            index = match.end()
        if index < len(text):
            out.append(text[index:])
        return out

    @staticmethod
    def _is_ascii_only(text: str) -> bool:
        return all(ord(ch) <= 0x7F for ch in text)

    @staticmethod
    def _contains_non_ascii(text: str) -> bool:
        return any(ord(ch) > 0x7F for ch in text)

    def _resolve_dynamic_date_value(self, token: str) -> str | None:
        alias = self.dynamic_date_aliases.get(token.lower())
        if alias is None:
            return None
        target = date.today() + timedelta(days=alias.offset_days)
        canonical = target.strftime("%d-%m-%Y")
        base_value = self.calendar_map.get(canonical)
        if base_value is None:
            return None
        if alias.intro is None:
            return base_value
        prefix = self.default_calendar_intro + " "
        if base_value.startswith(prefix):
            return alias.intro + base_value[len(self.default_calendar_intro):]
        return f"{alias.intro}, {base_value}"

    def _resolve_exact_token_key(self, token: str) -> str | None:
        if self._resolve_dynamic_date_value(token) is not None:
            return token
        if token in self.exact_token_map:
            return token
        if self._is_ascii_only(token):
            lower = token.lower()
            if lower != token and lower in self.exact_token_map:
                return lower
        return None

    def _resolve_composable_key(self, token: str) -> str | None:
        if token in self.clafrica_token_map:
            return token
        if self._is_ascii_only(token):
            lower = token.lower()
            if lower != token and lower in self.clafrica_token_map:
                return lower
        return None

    def _mapped_value_for_canonical_key(self, key: str) -> str | None:
        return self.exact_token_map.get(key) or self._resolve_dynamic_date_value(key)

    def _mapped_composable_value_for_canonical_key(self, key: str) -> str | None:
        return self.clafrica_token_map.get(key)

    def _apply_calendar_mappings(self, text: str) -> str:
        if not text:
            return text

        def replace(match: re.Match[str]) -> str:
            day = int(match.group(1))
            month = int(match.group(3))
            year = int(match.group(4))
            canonical = f"{day:02d}-{month:02d}-{year:04d}"
            return self.calendar_map.get(canonical, match.group(0))

        return self.calendar_pattern.sub(replace, text)

    def _apply_phrase_mappings(self, text: str) -> str:
        if not text:
            return text
        result = text
        changed = True
        while changed:
            changed = False
            for pattern, replacement in self.phrase_patterns_sorted:
                next_result = pattern.sub(replacement, result)
                if next_result != result:
                    result = next_result
                    changed = True
                    break
        return result

    def _get_longest_trailing_prefix(self, token: str) -> str | None:
        best: str | None = None
        lower_token = token.lower()
        for index in range(len(token)):
            suffix = token[index:]
            suffix_lower = lower_token[index:]
            ascii_suffix = self._is_ascii_only(suffix)
            matches = any(
                key.startswith(suffix)
                or (
                    ascii_suffix
                    and self._is_ascii_only(key)
                    and key.lower().startswith(suffix_lower)
                )
                for key in self.compositional_keys_sorted
            )
            if matches and (best is None or len(suffix) > len(best)):
                best = suffix
        return best

    def _get_longest_trailing_exact_key(self, token: str) -> str | None:
        best: str | None = None
        for index in range(len(token)):
            suffix = token[index:]
            if self._resolve_composable_key(suffix) is not None:
                if best is None or len(suffix) > len(best):
                    best = suffix
        return best

    def _get_ambiguous_trailing_suffix(self, token: str) -> str | None:
        best: str | None = None
        for index in range(len(token)):
            suffix = token[index:]
            canonical = self._resolve_composable_key(suffix)
            if canonical is not None and canonical in self.ambiguous_keys:
                if best is None or len(suffix) > len(best):
                    best = suffix
        return best

    def _apply_mapping_to_token(self, token: str) -> str:
        if not token:
            return token

        dynamic = self._resolve_dynamic_date_value(token)
        if dynamic is not None:
            return dynamic

        direct = self._resolve_exact_token_key(token)
        if direct is not None:
            return self._mapped_value_for_canonical_key(direct) or token

        match = re.fullmatch(r"^([a-zA-Z]+\*?)([1-9])([1-9])$", token)
        if match is not None:
            combined = "".join(match.groups())
            resolved = self._resolve_exact_token_key(combined)
            if resolved is not None:
                return self._mapped_value_for_canonical_key(resolved) or token

        match = re.fullmatch(r"^([a-zA-Z]+\*?)([1-9])$", token)
        if match is not None:
            combined = "".join(match.groups())
            resolved = self._resolve_exact_token_key(combined)
            if resolved is not None:
                return self._mapped_value_for_canonical_key(resolved) or token

        return self._apply_compositional_mapping_to_token(token)

    def _apply_compositional_mapping_to_token(self, token: str) -> str:
        if not token:
            return token
        if self._contains_non_ascii(token):
            return token

        result = token
        changed = True
        while changed:
            changed = False
            for key in self.compositional_keys_sorted:
                if len(key) > len(result) or key not in result:
                    continue
                next_result = result.replace(key, self.clafrica_token_map[key])
                if next_result != result:
                    result = next_result
                    changed = True
                    break
        return result

    def _apply_live_mapping_to_trailing_token(self, token: str) -> str:
        if not token:
            return token

        canonical = self._resolve_exact_token_key(token)
        if canonical is not None:
            if canonical in self.ambiguous_keys:
                return token
            return self._mapped_value_for_canonical_key(canonical) or token

        exact_trailing_key = self._get_longest_trailing_exact_key(token)
        exact_canonical = (
            self._resolve_composable_key(exact_trailing_key)
            if exact_trailing_key is not None
            else None
        )
        if (
            exact_trailing_key is not None
            and exact_canonical is not None
            and exact_canonical not in self.ambiguous_keys
        ):
            prefix = token[:-len(exact_trailing_key)]
            mapped_suffix = self._mapped_composable_value_for_canonical_key(exact_canonical) or exact_trailing_key
            return self._apply_compositional_mapping_to_token(prefix) + mapped_suffix

        ambiguous_suffix = self._get_ambiguous_trailing_suffix(token)
        if ambiguous_suffix is not None:
            prefix = token[:-len(ambiguous_suffix)]
            return self._apply_compositional_mapping_to_token(prefix) + ambiguous_suffix

        prefix_suffix = self._get_longest_trailing_prefix(token)
        if prefix_suffix is not None:
            prefix = token[:-len(prefix_suffix)]
            return self._apply_compositional_mapping_to_token(prefix) + prefix_suffix

        return self._apply_mapping_to_token(token)

    def _finalize_token(self, token: str) -> str:
        if not token:
            return token
        current = token
        changed = True
        while changed:
            changed = False
            exact_trailing_key = self._get_longest_trailing_exact_key(current)
            exact_canonical = (
                self._resolve_composable_key(exact_trailing_key)
                if exact_trailing_key is not None
                else None
            )
            if exact_trailing_key is not None and exact_canonical is not None:
                prefix = current[:-len(exact_trailing_key)]
                mapped_suffix = self._mapped_composable_value_for_canonical_key(exact_canonical) or exact_trailing_key
                next_value = self._apply_compositional_mapping_to_token(prefix) + mapped_suffix
                if next_value != current:
                    current = next_value
                    changed = True
                    continue

            fully_mapped = self._apply_mapping_to_token(current)
            if fully_mapped != current:
                current = fully_mapped
                changed = True
        return current

    def apply_mapping(self, text: str, preserve_ambiguous_trailing_token: bool = False) -> str:
        if not text:
            return text
        sequence_mapped = self._apply_phrase_mappings(self._apply_calendar_mappings(text))
        segments = self._split_with_whitespace(sequence_mapped)
        trailing_index = len(segments) - 1 if sequence_mapped and not sequence_mapped[-1].isspace() else -1
        out: list[str] = []
        for index, segment in enumerate(segments):
            if segment.isspace():
                out.append(segment)
            elif preserve_ambiguous_trailing_token and index == trailing_index:
                out.append(self._apply_live_mapping_to_trailing_token(segment))
            else:
                out.append(self._apply_mapping_to_token(segment))
        return "".join(out)

    def finalize_input(self, text: str) -> str:
        if not text:
            return text
        sequence_mapped = self._apply_phrase_mappings(self._apply_calendar_mappings(text))
        return "".join(
            segment if segment.isspace() else self._finalize_token(segment)
            for segment in self._split_with_whitespace(sequence_mapped)
        )

    def auto_complete_exact_text(self, text: str) -> str | None:
        if not text:
            return None

        if text in self.phrase_map and text not in self.ambiguous_phrase_keys:
            return self.phrase_map[text]

        canonical = self._resolve_exact_token_key(text)
        if canonical is None:
            return None
        if canonical in self.ambiguous_keys:
            return None
        return self._mapped_value_for_canonical_key(canonical)

    def would_transform_with_appended_text(self, text: str, appended: str) -> bool:
        candidate = f"{text}{appended}"
        if not candidate:
            return False

        auto_completed = self.auto_complete_exact_text(candidate)
        if auto_completed is not None and auto_completed != candidate:
            return True

        return self.finalize_input(candidate) != candidate

    def get_shortcut_hints(self, prefix: str, limit: int = 6) -> list[ShortcutHint]:
        if not prefix:
            return []

        prefix_lower = prefix.lower()
        exact_case: list[ShortcutHint] = []
        case_folded: list[ShortcutHint] = []
        for shortcut in self.shortcut_keys_sorted:
            if len(shortcut) <= len(prefix):
                continue
            if shortcut.startswith(prefix):
                exact_case.append(
                    ShortcutHint(prefix=prefix, shortcut=shortcut, remaining=shortcut[len(prefix):])
                )
                continue
            if self._is_ascii_only(shortcut) and shortcut.lower().startswith(prefix_lower):
                case_folded.append(
                    ShortcutHint(prefix=prefix, shortcut=shortcut, remaining=shortcut[len(prefix):])
                )
            if len(exact_case) >= limit:
                break
        return (exact_case + case_folded)[:limit]
