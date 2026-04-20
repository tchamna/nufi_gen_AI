# Repo Cleanup Candidates

This file is a review list, not an auto-delete list.

## Safe To Ignore Locally

These are generated or scratch outputs and are now ignored in `.gitignore`:

- `log_capture.txt`
- `cleaned/`
- `tmp_*`
- `android-keyboard/tmp_*.txt`
- `main_file.unique.txt`
- `main_file1.txt`
- `main_file2.txt`
- `data/nufi_top_100*`
- `data/nufi_unique_words*`
- `data/nufi_wordcloud*`
- `docs/*_latest.csv`

## Files To Review Before Keeping In Git

These are likely maintenance-only or export artifacts. Keep them only if they are still part of an intentional workflow:

- `nufi_language_model_text_generation_ngram_chatgpt.py`
- `scripts/generate_real_wordcloud.py`
- `scripts/generate_top_bar_chart.py`
- `scripts/rebuild_cleaned_corpus.py`
- `scripts/export_training_corpus_with_sources.py`
- generated corpus exports under `docs/`
- prebuilt pickle files under `data/Nufi/` other than the API model actually used in deploy

## Pipeline Rules

The production path should stay small:

1. runtime code
2. runtime data
3. one CI / deploy workflow
4. tests

Anything outside that path should either:

- move under `scripts/`
- be generated on demand
- be ignored locally
- or be deleted if nobody uses it anymore
