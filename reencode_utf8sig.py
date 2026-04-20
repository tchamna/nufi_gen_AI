from pathlib import Path
files = ['tmp_cleaned_utf8.txt','tmp_original.txt','tmp_diff.txt']
for f in files:
    p = Path(f)
    if p.exists():
        text = p.read_text(encoding='utf-8')
        p.write_text(text, encoding='utf-8-sig')
        print(f'Rewrote {f} with utf-8-sig')
    else:
        print(f'{f} missing')
