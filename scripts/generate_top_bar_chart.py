"""Generate a horizontal bar chart for the top N Nufī words.

Usage: python scripts/generate_top_bar_chart.py
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager

in_path = Path('data/nufi_top_100_no_numerics.txt')
out_png = Path('data/nufi_top_100_bar.png')
out_svg = Path('data/nufi_top_100_bar.svg')

if not in_path.exists():
    raise SystemExit(f'missing input file: {in_path}')

items = []
for ln in in_path.read_text(encoding='utf-8').splitlines():
    if not ln.strip():
        continue
    tok, cnt = ln.split('\t')
    try:
        cnt = int(cnt)
    except Exception:
        cnt = 1
    items.append((tok, cnt))

# Configuration: top-N to display and source text for the title
REQUESTED_TOP_N = 30
SOURCE = "From Shck Tchamna Nufī Dictionary"

# use the smaller of requested N and available items
TOP_N = min(REQUESTED_TOP_N, len(items)) if items else 0
if TOP_N == 0:
    raise SystemExit('no items to plot')

words, counts = zip(*items[:TOP_N])

# try to pick a Unicode-capable font
try:
    font_path = font_manager.findfont('DejaVu Sans')
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
except Exception:
    pass

fig, ax = plt.subplots(figsize=(12, 10))
y_pos = list(range(len(words)-1, -1, -1))
bars = ax.barh(y_pos, counts[::-1], align='center', color='tab:blue')
ax.set_yticks(y_pos)
ax.set_yticklabels(list(words[::-1]))
ax.invert_yaxis()
ax.set_xlabel('Frequency')
ax.set_title(f"Top {TOP_N} Nufī Words (Source: {SOURCE})")
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# make room on the right for labels and ensure labels don't overlap
max_count = max(counts)
ax.set_xlim(0, max_count * 1.12)
labels = [str(v) for v in counts[::-1]]
try:
    # matplotlib >=3.4
    ax.bar_label(bars, labels=labels, padding=6, fontsize=10)
except Exception:
    # fallback manual placement
    for i, v in enumerate(counts[::-1]):
        ax.text(v + max_count * 0.01, i, str(v), va='center', fontsize=10)

fig.tight_layout()
fig.savefig(out_png, dpi=200)
fig.savefig(out_svg)
print('Wrote', out_png, 'and', out_svg)
