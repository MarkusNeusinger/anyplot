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

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

```python
# Landscape — default (16:9)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)   # → 3200 × 1800 px

# Square — only for symmetric plots (heatmap, jointplot, pairplot, etc.)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400)     # → 2400 × 2400 px
```

**Do not use `bbox_inches="tight"` on `savefig`.** It silently trims the canvas (~30–50 px per axis → 3200×1800 becomes ~3160×1760) and was the documented cause of every seaborn drift in the May 2026 fan-out. Use `bbox_inches=None` (the explicit default) and let `figsize × dpi` produce the exact target. If you need to control padding, use `fig.subplots_adjust(...)` inside the figure or `sns.despine(...)` for spine layout.

For figure-level seaborn plots (`relplot`, `catplot`, `displot`), pass the **same** canvas size via `height=` / `aspect=`:

```python
# Landscape: aspect=16/9 ≈ 1.778, height controls the figure's height in inches; pick height=4.5 → width=8
g = sns.relplot(..., height=4.5, aspect=16/9)
g.figure.set_dpi(400)

# Square: aspect=1, height=6 → 2400×2400
g = sns.relplot(..., height=6, aspect=1)
g.figure.set_dpi(400)
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
plt.savefig(f'plot-{THEME}.png', dpi=400)  # bbox_inches MUST stay default (None) — see "Canvas" above
```

## Sizing for 3200×1800 px (starting values — adjust per plot, review-loop tunes)

```python
# Text sizes (seaborn uses matplotlib underneath) — title kept compact to avoid
# overflow of the long mandated "{spec-id} · python · seaborn · anyplot.ai" title.
ax.set_title(title, fontsize=12, fontweight='medium')
ax.set_xlabel(x_label, fontsize=10)
ax.set_ylabel(y_label, fontsize=10)
ax.tick_params(axis='both', labelsize=8)
# Legend at 8pt — skip for single-series plots (no labeled artists → warning)
if len(ax.get_legend_handles_labels()[0]) > 1:
    ax.legend(fontsize=8)

# Or use sns.set_context for global scaling
sns.set_context("notebook", font_scale=1.0)

# Element sizes in seaborn functions (density-aware — see default-style-guide.md)
sns.scatterplot(..., s=100)           # marker size, 60-150 typical
sns.lineplot(..., linewidth=2.5)      # line width

# Spine removal (default: remove top + right)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Grid (subtle, y-axis preferred)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
```

See `prompts/default-style-guide.md` "Proportional Sizing" for the review-step criteria.

## API Compatibility (0.14+)

```python
# WARNING: palette without hue
sns.boxplot(data=df, x='group', y='value', palette='Set2')  # Warning

# CORRECT: hue with palette
sns.boxplot(data=df, x='group', y='value', hue='group', palette='Set2', legend=False)
```

## Colors

Use the anyplot palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
# anyplot palette — canonical order, first series always #009E73
ANYPLOT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
color = ANYPLOT_PALETTE[0]  # '#009E73'
sns.scatterplot(data=df, x='x', y='y', color=color)

# Multi-series (hue)
sns.scatterplot(data=df, x='x', y='y', hue='category', palette=ANYPLOT_PALETTE[:N])

# Set once globally for a whole figure
sns.set_palette(ANYPLOT_PALETTE)
```

## Continuous-data Palettes (anyplot cmaps only)

```python
from matplotlib.colors import LinearSegmentedColormap

# Sequential / single-polarity (intensity, magnitude, density)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Diverging (signed deviations, residuals, correlations) — midpoint theme-adaptive
midpoint = "#FAF8F1" if THEME == "light" else "#1A1A17"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", midpoint, "#4467A3"])

# Use via cmap=imprint_seq / cmap=imprint_div on heatmap, kdeplot, etc.
# Forbidden: any other cmap (viridis/cividis/BrBG/Reds/Blues/Greens/jet/hsv/rainbow).
```

Never use seaborn's `palette='Set2'`/`'tab10'`/`'colorblind'` for categorical data — they override the anyplot brand identity. The only continuous cmaps allowed are the two anyplot palette-derived cmaps above.

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
        "grid.alpha":       0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# After plotting
plt.savefig(f'plot-{THEME}.png', dpi=400, facecolor=PAGE_BG)  # do NOT add bbox_inches='tight'
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/seaborn.py` — executed twice by the pipeline with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (seaborn is PNG-only).
