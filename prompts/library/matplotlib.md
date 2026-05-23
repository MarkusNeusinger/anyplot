# matplotlib

## Interactive Spec Handling

matplotlib produces **static PNG only**. When implementing specs that mention interactive features:

- Specs with primary interactivity (hover, zoom, click, brush) → **NOT_FEASIBLE**
- Specs with animation → Use small multiples or faceted grid as static alternative
- Mixed specs (static + interactive) → Implement static features only, omit interactive silently
- **NEVER** simulate tooltips, hover states, or controls. See AR-08 in `prompts/quality-criteria.md`

---

## Import

```python
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

```python
# Landscape — default for most plots (16:9)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)   # → 3200 × 1800 px

# Square — only for symmetric plots (pie, radar, heatmap, maze, …)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400)     # → 2400 × 2400 px
```

Pick one based on the spec; do not invent a third aspect. Multi-panel layouts must keep the figure dims constant (use `gridspec` / `subplot_mosaic` to subdivide internally).

**Do not use `bbox_inches="tight"` on `savefig`.** It silently trims the canvas (typically ~30–50 px on each axis → e.g. 3200×1800 becomes 3160×1760) and was the documented cause of every matplotlib drift in the May 2026 fan-out. Use `bbox_inches=None` (the explicit default) instead, and let `figsize × dpi` produce the exact target. If you need to control padding, use `fig.subplots_adjust(left=…, right=…, top=…, bottom=…)` *inside* the figure.

## Plot Methods

Use **Axes methods** (not pyplot):

```python
# Correct
ax.scatter(x, y)
ax.plot(x, y)
ax.bar(x, y)

# Wrong
plt.scatter(x, y)
```

## Save

```python
plt.savefig(f'plot-{THEME}.png', dpi=400)  # bbox_inches MUST stay default (None) — see "Canvas" above
```

## Sizing for 3200×1800 px (starting values — adjust per plot, review-loop tunes)

```python
# Text sizes — title kept compact because the mandated "{spec-id} · python · matplotlib · anyplot.ai"
# title is ~67 chars and would overflow at 16+pt on the 3200px-wide canvas.
# Title fontsize scales linearly with title length so a "{Descriptive Title} · " prefix or a
# long {spec-id} doesn't overflow — compute from the exact title string at codegen time:
#   title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight='medium')
ax.set_xlabel(x_label, fontsize=10)
ax.set_ylabel(y_label, fontsize=10)
ax.tick_params(axis='both', labelsize=8)
# Legend at 8pt — skip ax.legend() for single-series plots (avoids the
# "No artists with labels found to put in legend" warning)
if len(ax.get_legend_handles_labels()[0]) > 1:
    ax.legend(fontsize=8)

# Element sizes
ax.scatter(x, y, s=100, edgecolors='white', linewidth=0.5)  # s=60-150 (density-aware)
ax.plot(x, y, linewidth=2.5)   # ~2-3 for primary lines

# Grid (subtle, y-axis preferred)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

# Spine removal (default: remove top + right)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
```

See `prompts/default-style-guide.md` "Proportional Sizing" for the review-step criteria — short labels at oversized fonts cost points; long descriptive labels at normal fonts are fine.

## Styling

```python
ax.set_xlabel(x_label, fontsize=10)
ax.set_ylabel(y_label, fontsize=10)
ax.set_title(title, fontsize=12, fontweight='medium')
ax.legend(fontsize=8)  # if needed (omit for single-series)
plt.tight_layout()
```

## API Compatibility (3.9+)

```python
# DEPRECATED: labels in boxplot
ax.boxplot(data, labels=group_names)  # Wrong

# CORRECT: use tick_labels
ax.boxplot(data, tick_labels=group_names)  # Right
```

## Colors

Use the anyplot palette (see `prompts/default-style-guide.md` "Categorical Palette" for the canonical list). First series is **always** `#009E73`.

```python
# anyplot palette — use positions 1→N in canonical order
ANYPLOT_PALETTE = ['#009E73', '#9418DB', '#B71D27', '#16B8F3',
                   '#99B314', '#D359A7', '#BA843E']

# Single-series: always position 1 (brand green)
color = ANYPLOT_PALETTE[0]  # '#009E73'

# Multi-series: take the first N colors in order, don't cherry-pick
ax.set_prop_cycle(color=ANYPLOT_PALETTE[:N])

# Continuous data — only the two anyplot palette-derived cmaps are allowed
# (no viridis/cividis/BrBG/Reds/Blues/Greens/jet/hsv/rainbow):
from matplotlib.colors import LinearSegmentedColormap
anyplot_seq = LinearSegmentedColormap.from_list("anyplot_seq", ["#009E73", "#003D94"])
anyplot_div = LinearSegmentedColormap.from_list("anyplot_div", ["#BB0D22", "#A2A598", "#007AD9"])
# Sequential / single-polarity heatmaps: cmap=anyplot_seq
# Diverging (signed deviations, residuals, correlations):    cmap=anyplot_div
```

## Theme-adaptive Chrome (matplotlib mapping)

The pipeline runs each implementation twice: `ANYPLOT_THEME=light` → `plot-light.png`, `ANYPLOT_THEME=dark` → `plot-dark.png`. Backgrounds, text, grid, spines, legend frames, and annotation boxes all flip; only the anyplot palette data colors stay constant.

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED   = "#6B6A63" if THEME == "light" else "#A8A79F"

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.set_title(..., color=INK)
ax.set_xlabel(..., color=INK); ax.set_ylabel(..., color=INK)
ax.tick_params(colors=INK_SOFT, labelcolor=INK_SOFT)
for s in ('left', 'bottom'): ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.15, color=INK)

leg = ax.legend(...)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Annotations (sparingly, only when spec requests them)
ax.annotate(..., color=INK,
            bbox=dict(facecolor=ELEVATED_BG, edgecolor=INK_SOFT, alpha=0.9))

plt.savefig(f'plot-{THEME}.png', dpi=400, facecolor=PAGE_BG)  # do NOT add bbox_inches='tight'
```

## Output Files

- Implementation file: `plots/{spec-id}/implementations/matplotlib.py` — single source, executed by the pipeline twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (matplotlib is PNG-only).
