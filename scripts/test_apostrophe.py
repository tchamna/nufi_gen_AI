from keep_only_nufi_v2 import LanguageSegmenter
seg = LanguageSegmenter()
samples = ["bɑ́mfɑ́'", "bɑ́mfɑ́’", "a'", "fa'á"]
for s in samples:
    out = seg.keep_only_nufi_text(s)
    print(repr(s), '->', repr(out))
