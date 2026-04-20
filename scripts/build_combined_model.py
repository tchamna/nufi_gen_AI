#!/usr/bin/env python3
# Build and save the combined n-gram model for the API
import os
import pickle
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.getcwd())
import nufi_model as nm

BASE = os.getcwd()
print('Loading corpus...')
cleaned, tokens = nm.load_corpus(BASE)
print('Loaded', len(tokens), 'sentences')

print('Building combined model (2..5)...')
model = nm.build_combined_model(tokens, max_n=5)

out_path = os.path.join(BASE, 'data', 'Nufi', 'Nufi_language_model_api.pickle')
print('Saving model to', out_path)
nm.save_model(model, out_path)
print('Saved model keys=', len(model))

seed = 'ǒ mɑ́'
print('Test generate for seed:', seed)
try:
    out = nm.generate_text_from_model(model, seed, n=5)
    print('Generation result:', out)
except Exception as e:
    print('Generation error:', e)
