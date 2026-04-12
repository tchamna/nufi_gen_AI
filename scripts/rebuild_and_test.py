import os
import nufi_model as nm

base_dir = os.getcwd()
print('base_dir=', base_dir)
CLEANED, TOKENS = nm.load_corpus(base_dir)
print('cleaned len=', len(CLEANED), 'tokens len=', len(TOKENS))
seed = 'ǒ mɑ́'
seed_tokens = seed.split()

results = {}
for n in range(2, 7):
    print('\n--- testing n=', n)
    model = nm.build_ngram_model(TOKENS, n=n)
    # check if context key exists
    key = tuple(seed_tokens[-n+1:]) if n-1 > 0 else tuple()
    has_context = bool(model.get(key))
    print('context key=', key, 'has_context=', has_context)
    if has_context:
        print('sample next tokens:', list(model[key].items())[:10])
    out = nm.generate_text_from_model(model, seed, n=n)
    print('generate_text ->', out)
    # save model for this n
    path = os.path.join(base_dir, 'data', 'Nufi', f'Nufi_language_model_{n}gram_test.pickle')
    nm.save_model(model, path)
    print('saved model to', path)
    results[n] = (has_context, out)

print('\nSummary:')
for n, (has_context, out) in results.items():
    print(n, has_context, out)
