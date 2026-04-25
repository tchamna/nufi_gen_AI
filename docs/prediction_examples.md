# Prediction algorithm — practical examples

This document explains how the production API picks next-word predictions from the combined n-gram model (the `Nufi_language_model_api.pickle` used by the API).

Summary
- The API uses a combined/interpolated n-gram model (orders 2..5 by default).
- At prediction time the algorithm:
  1. Finds the longest available context(s) matching the last K tokens of the input.
  2. Collects distributions for several context lengths (longest → shorter).
  3. Computes blend weights and merges the distributions into a single probability distribution.
  4. Samples (or takes argmax) from the merged distribution using the `temperature` parameter.

Key functions (see `nufi_model.py`)
- `_find_choices_with_length` — locate longest matching context(s).
- `_interpolate_ngram_choices` — collect levels and merge with weights.
- `_weights_for_backoff_levels` — returns blend weights for levels.
- `_sample_word` — performs temperature-adjusted selection.

Numeric toy example

Imagine the model contains these next-word distributions for a given seed (longest→shortest):

- 4-gram (context length 4): {'X': 0.80, 'Y': 0.20}
- 3-gram (context length 3): {'X': 0.20, 'Z': 0.80}
- 2-gram (context length 2): {'Y': 0.60, 'Z': 0.40}
- unigram (empty context):   {'X': 0.50, 'Y': 0.30, 'Z': 0.20}

Step 1 — collect levels
- Available levels (from longest to shortest): 4, 3, 2, 1.

Step 2 — compute blend weights
- For 4 levels, the implementation uses a geometric raw vector [1, 0.5, 0.25, 0.125] normalized to sum=1.
- Normalized weights ≈ [0.5333, 0.2667, 0.1333, 0.0667].

Step 3 — merge distributions (per-word)
- Compute merged probability for each word as sum_k alpha_k * p_k(word):

  - P(X) = 0.5333*0.80 + 0.2667*0.20 + 0.1333*0 + 0.0667*0.50 ≈ 0.5133
  - P(Y) = 0.5333*0.20 + 0.2667*0     + 0.1333*0.60 + 0.0667*0.30 ≈ 0.2067
  - P(Z) = 0.5333*0    + 0.2667*0.80 + 0.1333*0.40 + 0.0667*0.20 ≈ 0.2799

These sum to ~1.0. The merged distribution is used for selection.

Step 4 — selection (temperature)
- If `temperature <= 0` the algorithm picks the highest-probability word (`argmax`), here `X`.
- For `temperature > 0` probabilities are adjusted by p' = p ** (1/temperature) then re-normalized and sampled.

Why this works well
- Long contexts (4–5 grams) capture precise continuations when present.
- Shorter contexts provide robust fallback when long contexts are sparse.
- Interpolation blends signals instead of hard backoff, avoiding brittle decisions when data is limited.

Reproduce the numeric example quickly
Run this Python snippet (inside the project venv) to compute merged probabilities with the same logic:

```python
from math import isclose

# Toy per-level distributions (longest->shortest)
levels = [
    ({'X':0.80,'Y':0.20}, 4),
    ({'X':0.20,'Z':0.80}, 3),
    ({'Y':0.60,'Z':0.40}, 2),
    ({'X':0.50,'Y':0.30,'Z':0.20}, 1),
]

# compute geometric raw weights for n levels
n = len(levels)
raw = [0.5**i for i in range(n)]
s = sum(raw)
weights = [r/s for r in raw]

merged = {}
for (dist, k), alpha in zip(levels, weights):
    for w,p in dist.items():
        merged[w] = merged.get(w, 0.0) + alpha * p

print('weights=', [round(w,4) for w in weights])
print('merged=', {w: round(p,4) for w,p in merged.items()})
print('sum=', round(sum(merged.values()),4))
```

Where to look in the code
- Generation & interpolation: `nufi_model.py` — `_find_choices_with_length`, `_interpolate_ngram_choices`, `_weights_for_backoff_levels`, `_sample_word`.
- Model builder: `build_combined_model()` (builds the combined lookup across orders).

If you'd like I can add an interactive notebook that demonstrates several seeds, shows the levels available for each seed, prints the per-level distributions and merged result, and compares `temperature=0` vs `temperature=1` selections.

***
Document created by the tooling team to help users understand next-word prediction behavior.
