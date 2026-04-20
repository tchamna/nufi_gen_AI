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

**Authentication (pick one):**

1. **Single secret `AZURE_CREDENTIALS`** — must be **valid JSON** with `clientId`, `clientSecret`, `subscriptionId`, and `tenantId`. The reliable way to produce that shape is Azure CLI with **`--sdk-auth`** (not the default `create-for-rbac` output, which uses `appId` / `password` / `tenant` and often omits `subscriptionId`):

   ```bash
   az ad sp create-for-rbac \
     --name "github-nufi-deploy" \
     --role contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RG>/providers/Microsoft.Web/sites/<APP_NAME> \
     --sdk-auth
   ```

   Paste the **entire** JSON object into the `AZURE_CREDENTIALS` secret (no markdown fences, no extra text).

2. **Four repository secrets** (same values as in that JSON, split out): `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`. If all four are set, they take precedence over `AZURE_CREDENTIALS`.

The workflow runs `az login --service-principal`, then `azure/webapps-deploy` without a publish profile.

If `AZURE_WEBAPP_NAME` is not set, the deploy step is skipped and CI still passes.

## Manual Run

Use **Actions -> CI / Deploy -> Run workflow** to trigger the workflow manually.
