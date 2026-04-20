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
    title_text = "Nufī top 100 wordcloud"
    subtitle_text = f"(Source: From Shck Tchamna Nufi Dictionary) — {source}"
    try:
        pos = svg.find('</rect>')
        title_svg = f'<text x="50" y="40" font-size="36" fill="#333">{title_text}</text>\n'
        subtitle_svg = f'<text x="50" y="72" font-size="20" fill="#666">{subtitle_text}</text>\n'
        inject = title_svg + subtitle_svg
        # Insert title/subtitle as an overlay at the end so it renders on top
        close_tag = svg.rfind('</svg>')
        if close_tag != -1:
            header_rect = f'<rect x="0" y="0" width="100%" height="96" style="fill:white;fill-opacity:0.95"></rect>\n'
            svg = svg[:close_tag] + '\n' + header_rect + inject + svg[close_tag:]
        else:
            # fallback: keep previous injection position (after background rect)
            if pos != -1:
                pos += len('</rect>')
                svg = svg[:pos] + '\n' + inject + svg[pos:]
            else:
                open_tag_end = svg.find('>')
                if open_tag_end != -1:
                    svg = svg[:open_tag_end+1] + '\n' + inject + svg[open_tag_end+1:]
    except Exception:
        pass
    out_svg.write_text(svg, encoding='utf-8')

    # add title overlay to the PNG by expanding canvas upward and drawing text
    try:
        img = Image.open(out_png).convert('RGBA')
        title_h = 96
        new_w, new_h = img.width, img.height + title_h
        new_img = Image.new('RGBA', (new_w, new_h), 'WHITE')
        new_img.paste(img, (0, title_h))
        draw = ImageDraw.Draw(new_img)
        # draw a semi-opaque white header strip behind title/subtitle to keep them readable
        try:
            draw.rectangle((0, 0, new_w, title_h), fill=(255, 255, 255, 230))
        except Exception:
            # fallback if RGBA not supported
            draw.rectangle((0, 0, new_w, title_h), fill=(255, 255, 255))
        try:
            if font_path:
                title_font = ImageFont.truetype(font_path, 36)
                subtitle_font = ImageFont.truetype(font_path, 18)
            else:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        # draw title centered on first line
        # compute title bbox using textbbox for Pillow compatibility
        try:
            bbox = draw.textbbox((0, 0), title_text, font=title_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = (draw.textlength(title_text, font=title_font), 36)
        x = max(10, (new_w - text_w) // 2)
        y = 10
        draw.text((x, y), title_text, fill=(51, 51, 51), font=title_font)
        # draw subtitle below using textbbox
        try:
            sbbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            sub_w = sbbox[2] - sbbox[0]
            sub_h = sbbox[3] - sbbox[1]
        except Exception:
            sub_w, sub_h = (draw.textlength(subtitle_text, font=subtitle_font), 18)
        sub_x = max(10, (new_w - sub_w) // 2)
        sub_y = y + text_h + 6
        draw.text((sub_x, sub_y), subtitle_text, fill=(102, 102, 102), font=subtitle_font)
        # save back to PNG (replace)
        new_img.convert('RGB').save(out_png)
    except Exception as e:
        print('PNG title overlay failed:', e)

    print('Wrote', out_png, 'and', out_svg)
except Exception as e:
    print('Wordcloud generation failed:', type(e).__name__, e)
    print('Ensure `wordcloud matplotlib pillow fonttools` are installed in the venv (pip install -r requirements-dev.txt)')
    raise
