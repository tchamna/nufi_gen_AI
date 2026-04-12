import os, sys, json
import nufi_model as nm

base_dir = os.getcwd()
CLEANED, TOKENS = nm.load_corpus(base_dir)
seed = 'ǒ mɑ́'
results = {}
chosen = None
chosen_n = None
MODEL_PATH = os.path.join(base_dir, 'data', 'Nufi', 'Nufi_language_model_api.pickle')

for n in range(2, 7):
    print(f'Building n={n} model...')
    model = nm.build_ngram_model(TOKENS, n=n)
    out = nm.generate_text_from_model(model, seed, n=n)
    print(f' n={n} -> {out}')
    results[n] = out
    if isinstance(out, str) and out.endswith('not in corpus'):
        # not working
        continue
    # produced continuation
    chosen = model
    chosen_n = n
    break

# If none produced continuation, pick the model with largest context coverage (heuristic: largest len(model))
if chosen is None:
    # pick n with largest model size
    sizes = {}
    for n in range(2,7):
        print(f'Building for size check n={n}...')
        m = nm.build_ngram_model(TOKENS, n=n)
        sizes[n] = len(m)
    best_n = max(sizes, key=lambda k: sizes[k])
    print('No continuation found; selecting largest model n=', best_n)
    chosen = nm.build_ngram_model(TOKENS, n=best_n)
    chosen_n = best_n

# Save chosen model to API path
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
with open(MODEL_PATH, 'wb') as f:
    import pickle
    pickle.dump(chosen, f)

summary = {
    'chosen_n': chosen_n,
    'results': results,
    'model_path': MODEL_PATH,
}
print('\nSAVE SUMMARY:')
print(json.dumps(summary, ensure_ascii=True, indent=2))
# Print a test generation with chosen model
print('\nTest generation with saved model:')
print(nm.generate_text_from_model(chosen, seed, n=chosen_n))
