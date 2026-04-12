import os
import nufi_model as nm
CLEANED,TOKENS = nm.load_corpus(os.getcwd())
seq = ('ǒ','mɑ́')
nexts = []
for s in TOKENS:
    for i in range(len(s)-1):
        if (s[i], s[i+1]) == seq:
            nxt = s[i+2] if i+2 < len(s) else None
            nexts.append(nxt)
print('occurrences=', len(nexts))
print('sample next tokens=', list(dict.fromkeys(nexts))[:50])
print('sample sentences containing seq=')
count=0
for sent in CLEANED:
    if 'ǒ mɑ́' in sent:
        print(' -', sent)
        count+=1
        if count>=10:
            break
