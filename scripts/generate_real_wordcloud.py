"""Generate packed wordcloud PNG and SVG from data/nufi_top_100_no_numerics.txt.

Usage: python scripts/generate_real_wordcloud.py
"""
from pathlib import Path
import hashlib

in_path = Path('data/nufi_top_100_no_numerics.txt')
out_png = Path('data/nufi_wordcloud_real.png')
out_svg = Path('data/nufi_wordcloud_real.svg')

if not in_path.exists():
    raise SystemExit(f'missing input file: {in_path}')

freqs = {}
for ln in in_path.read_text(encoding='utf-8').splitlines():
    if not ln.strip():
        continue
    tok, cnt = ln.split('\t')
    try:
        cnt = int(cnt)
    except Exception:
        cnt = 1
    freqs[tok] = cnt

try:
    from wordcloud import WordCloud
    import matplotlib.font_manager as fm
    from PIL import Image, ImageDraw, ImageFont

    # choose a Unicode-capable font if available
    try:
        font_path = fm.findfont('DejaVu Sans')
    except Exception:
        font_path = None

    wc = WordCloud(width=1600, height=900, background_color='white', prefer_horizontal=0.9,
                   colormap='plasma', relative_scaling=0.5, normalize_plurals=False,
                   font_path=font_path)
    wc = wc.generate_from_frequencies(freqs)

    # write the raster PNG first
    wc.to_file(str(out_png))

    # write SVG and inject a visible title near the top
    svg = wc.to_svg(embed_font=True)
    source = in_path.name if in_path is not None else 'unknown'
    title_text = f"Nufī top 100 wordcloud — source: {source}"
    try:
        pos = svg.find('</rect>')
        title_svg = f'<text x="50" y="40" font-size="36" fill="#333">{title_text}</text>\n'
        if pos != -1:
            pos += len('</rect>')
            svg = svg[:pos] + '\n' + title_svg + svg[pos:]
        else:
            # fallback: insert after opening <svg> tag
            open_tag_end = svg.find('>')
            if open_tag_end != -1:
                svg = svg[:open_tag_end+1] + '\n' + title_svg + svg[open_tag_end+1:]
    except Exception:
        pass
    out_svg.write_text(svg, encoding='utf-8')

    # add title overlay to the PNG by expanding canvas upward and drawing text
    try:
        img = Image.open(out_png).convert('RGBA')
        title_h = 64
        new_w, new_h = img.width, img.height + title_h
        new_img = Image.new('RGBA', (new_w, new_h), 'WHITE')
        new_img.paste(img, (0, title_h))
        draw = ImageDraw.Draw(new_img)
        try:
            if font_path:
                font = ImageFont.truetype(font_path, 36)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        text_w, text_h = draw.textsize(title_text, font=font)
        x = max(10, (new_w - text_w) // 2)
        y = (title_h - text_h) // 2
        draw.text((x, y), title_text, fill=(51, 51, 51), font=font)
        # save back to PNG (replace)
        new_img.convert('RGB').save(out_png)
    except Exception as e:
        print('PNG title overlay failed:', e)

    print('Wrote', out_png, 'and', out_svg)
except Exception as e:
    print('Wordcloud generation failed:', type(e).__name__, e)
    print('Ensure `wordcloud matplotlib pillow fonttools` are installed in the venv (pip install -r requirements-dev.txt)')
    raise
