import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import difflib

def extract_docx_text(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as z:
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = [t.text for t in root.findall('.//w:t', ns) if t.text]
            # join with spaces where paragraphs end
            paras = []
            for p in root.findall('.//w:p', ns):
                texts_p = [t.text for t in p.findall('.//w:t', ns) if t.text]
                if texts_p:
                    paras.append(''.join(texts_p))
            return '\n'.join(paras)


def main():
    if len(sys.argv) < 3:
        print('Usage: compare_docx.py <docx_path> <cleaned_txt_path>')
        sys.exit(2)
    docx = Path(sys.argv[1])
    cleaned = Path(sys.argv[2])
    out_orig = Path('tmp_original.txt')
    out_diff = Path('tmp_diff.txt')

    orig_text = extract_docx_text(docx)
    out_orig.write_text(orig_text, encoding='utf-8-sig')

    a_lines = orig_text.splitlines()
    cleaned_text = cleaned.read_text(encoding='utf-8')
    # ensure cleaned file is saved with UTF-8 BOM (utf-8-sig) for Windows compatibility
    cleaned.write_text(cleaned_text, encoding='utf-8-sig')
    b_lines = cleaned_text.splitlines()

    diff = difflib.unified_diff(a_lines, b_lines, fromfile='original', tofile='cleaned', lineterm='')
    diff_text = '\n'.join(diff)
    out_diff.write_text(diff_text, encoding='utf-8-sig')

    # simple token stats
    import re
    tokenize = lambda s: re.findall(r"\w+|[^	\s]", s, flags=re.UNICODE)
    a_tokens = tokenize(orig_text.lower())
    b_tokens = tokenize('\n'.join(b_lines).lower())
    a_set = set(a_tokens)
    b_set = set(b_tokens)
    removed = sorted(list(a_set - b_set))

    summary = [
        f'original_lines={len(a_lines)}',
        f'cleaned_lines={len(b_lines)}',
        f'original_tokens={len(a_tokens)}',
        f'cleaned_tokens={len(b_tokens)}',
        f'unique_removed_count={len(removed)}',
        'sample_removed=' + ', '.join(removed[:50])
    ]
    print('\n'.join(summary))
    print('\nDiff saved to tmp_diff.txt')

if __name__ == '__main__':
    main()
