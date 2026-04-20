# GitHub Actions

The repo now uses one workflow: `.github/workflows/ci.yml`.

## Flow

1. Install `requirements-dev.txt`
2. Build the training corpus export files
3. Build lexical reports and visuals
4. Upload those files as a GitHub Actions artifact
5. Run `pytest tests/ -q`
6. If the event is a push to `main` or `master`, optionally deploy to Azure

The uploaded artifact contains:

- `docs/training_corpus_unique_sentences_with_sources.txt`
- `docs/training_corpus_unique_sentences_with_sources.csv`
- `docs/training_corpus_unique_sentences_only.txt`
- `docs/training_corpus_unique_sentences_only.csv`
- `data/nufi_unique_words.txt`
- `data/nufi_unique_words_alpha.txt`
- `data/nufi_top_100.txt`
- `data/nufi_top_100_no_numerics.txt`
- `data/nufi_top_100_preview.txt`
- `data/nufi_top_100_bar.png`
- `data/nufi_top_100_bar.svg`
- `data/nufi_wordcloud_real.png`
- `data/nufi_wordcloud_real.svg`

## Azure Deploy Setup

Create these GitHub Actions settings:

- `AZURE_WEBAPP_NAME`: App Service name, as either a **repository variable** or a **repository secret** (both are supported)
- repository secret: `AZURE_CREDENTIALS` — JSON for a service principal that can deploy to that app (for example the output of `az ad sp create-for-rbac --name "<name>" --role contributor --scopes /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app> --sdk-auth`)

The workflow runs `azure/login` with that secret, then `azure/webapps-deploy` without a publish profile.

If `AZURE_WEBAPP_NAME` is not set, the deploy step is skipped and CI still passes.

## Manual Run

Use **Actions -> CI / Deploy -> Run workflow** to trigger the workflow manually.
