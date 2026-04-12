import os
import sys
from collections import Counter
import nufi_model as nm

base_dir = os.getcwd()
CLEANED, TOKENS = nm.load_corpus(base_dir)
seq = ('ǒ', 'mɑ́')
nexts = []
prevs = []
contexts = []
occ_sentences = []

window = 4
for sent_idx, s in enumerate(TOKENS):
    for i in range(len(s)-1):
        if (s[i], s[i+1]) == seq:
            # next token
            nxt = s[i+2] if i+2 < len(s) else None
            prev = s[i-1] if i-1 >= 0 else None
            nexts.append(nxt)
            prevs.append(prev)
            # context tokens
            start = max(0, i-window)
            end = min(len(s), i+3+window)  # include next and a bit after
            ctx = s[start:end]
            contexts.append(' '.join([t for t in ctx if t is not None]))
            # sentence
            occ_sentences.append(CLEANED[sent_idx])

# Summaries
next_counts = Counter(nexts)
prev_counts = Counter(prevs)

out_lines = []
out_lines.append(f"Search sequence: {' '.join(seq)}")
out_lines.append(f"Occurrences found: {len(nexts)}")
out_lines.append('\nNext-token counts (top 30):')
for tok, cnt in next_counts.most_common(30):
    out_lines.append(f"{repr(tok)} : {cnt}")
out_lines.append('\nPrev-token counts (top 30):')
for tok, cnt in prev_counts.most_common(30):
    out_lines.append(f"{repr(tok)} : {cnt}")
out_lines.append('\nSample contexts (up to 30):')
for c in contexts[:30]:
    out_lines.append(c)
out_lines.append('\nSample sentences containing sequence (up to 30):')
for s in occ_sentences[:30]:
    out_lines.append(s)

output = '\n'.join(out_lines)
# Write as UTF-8 to avoid terminal encoding errors
sys.stdout.buffer.write(output.encode('utf-8'))
