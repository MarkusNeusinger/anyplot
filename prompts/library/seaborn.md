# seaborn

## Interactive Spec Handling

seaborn produces **static PNG only** (via matplotlib). When implementing specs that mention interactive features:

- Specs with primary interactivity (hover, zoom, click, brush) → **NOT_FEASIBLE**
- Specs with animation → Use small multiples or faceted grid as static alternative
- Mixed specs (static + interactive) → Implement static features only, omit interactive silently
- **NEVER** simulate tooltips, hover states, or controls. See AR-08 in `prompts/quality-criteria.md`

---

## Import

```python
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
```

## Create Figure

```python
fig, ax = plt.subplots(figsize=(16, 9))
```

## Plot Methods

```python
# Axes-level (preferred)
sns.scatterplot(data=df, x='col_x', y='col_y', ax=ax)

# Figure-level (for complex layouts)
g = sns.relplot(data=df, x='col_x', y='col_y')
fig = g.figure
```

## Save

```python
plt.savefig(f'plot-{THEME}.png', dpi=300, bbox_inches='tight')
```

## Sizing for 4800×2700 px

```python
# Text sizes (seaborn uses matplotlib underneath)
ax.set_title(title, fontsize=24, fontweight='medium')
ax.set_xlabel(x_label, fontsize=20)
ax.set_ylabel(y_label, fontsize=20)
ax.tick_params(axis='both', labelsize=16)

# Or use sns.set_context for global scaling
sns.set_context("talk", font_scale=1.2)

# Element sizes in seaborn functions
sns.scatterplot(..., s=200)           # marker size
sns.lineplot(..., linewidth=3)        # line width

# Spine removal (default: remove top + right)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Grid (subtle, y-axis preferred)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
```

## API Compatibility (0.14+)

```python
# WARNING: palette without hue
sns.boxplot(data=df, x='group', y='value', palette='Set2')  # Warning

# CORRECT: hue with palette
sns.boxplot(data=df, x='group', y='value', hue='group', palette='Set2', legend=False)
```

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
# Okabe-Ito palette — canonical order, first series always #009E73
OKABE_ITO = ['#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442']

# Single-series
color = OKABE_ITO[0]  # '#009E73'
sns.scatterplot(data=df, x='x', y='y', color=color)

# Multi-series (hue)
sns.scatterplot(data=df, x='x', y='y', hue='category', palette=OKABE_ITO[:N])

# Set once globally for a whole figure
sns.set_palette(OKABE_ITO)
```

## Continuous-data Palettes (seaborn cmaps)

```python
# Sequential (perceptually uniform)
cmap='viridis'       # default
cmap='cividis'       # CVD-optimized alternative

# Diverging (centered on midpoint)
cmap='BrBG'          # ColorBrewer, anyplot default for diverging

# Single-polarity (ties to brand)
cmap='Blues' / 'Greens' / 'Reds'

# Forbidden: 'jet', 'hsv', 'rainbow' — not perceptually uniform
```

Never use seaborn's `palette='Set2'`/`'tab10'`/`'colorblind'` for categorical data — they override the Okabe-Ito brand identity. `'viridis'`, `'Blues'`, `'Greens'` are fine for **continuous** data only.

## Theme-adaptive Chrome (seaborn mapping)

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor":   PAGE_BG,
        "axes.edgecolor":   INK_SOFT,
        "axes.labelcolor":  INK,
        "text.color":       INK,
        "xtick.color":      INK_SOFT,
        "ytick.color":      INK_SOFT,
        "grid.color":       INK,
        "grid.alpha":       0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# After plotting
plt.savefig(f'plot-{THEME}.png', dpi=300, bbox_inches='tight', facecolor=PAGE_BG)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/seaborn.py` — executed twice by the pipeline with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (seaborn is PNG-only).
