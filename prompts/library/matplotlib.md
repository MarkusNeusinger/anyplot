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

## Create Figure

```python
fig, ax = plt.subplots(figsize=(16, 9))
```

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
plt.savefig(f'plot-{THEME}.png', dpi=300, bbox_inches='tight')
```

## Sizing for 4800×2700 px

```python
# Text sizes
ax.set_title(title, fontsize=24, fontweight='medium')
ax.set_xlabel(x_label, fontsize=20)
ax.set_ylabel(y_label, fontsize=20)
ax.tick_params(axis='both', labelsize=16)
ax.legend(fontsize=16)

# Element sizes
ax.scatter(x, y, s=200, edgecolors='white', linewidth=0.5)  # s=150-300
ax.plot(x, y, linewidth=3)   # linewidth=2-4 (not 1!)

# Grid (subtle, y-axis preferred)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

# Spine removal (default: remove top + right)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
```

## Styling

```python
ax.set_xlabel(x_label, fontsize=20)
ax.set_ylabel(y_label, fontsize=20)
ax.set_title(title, fontsize=24, fontweight='medium')
ax.legend(fontsize=16)  # if needed (omit for single-series)
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

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette" for the canonical list). First series is **always** `#009E73`.

```python
# Okabe-Ito palette — use positions 1→N in canonical order
OKABE_ITO = ['#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442']

# Single-series: always position 1 (brand green)
color = OKABE_ITO[0]  # '#009E73'

# Multi-series: take the first N colors in order, don't cherry-pick
ax.set_prop_cycle(color=OKABE_ITO[:N])

# Continuous data — Okabe-Ito is NOT used (causes banding):
#   Sequential: cmap='viridis' or 'cividis'
#   Diverging:  cmap='BrBG'
#   Heatmaps:   cmap='viridis' or single-polarity 'Reds'/'Blues'
#   Forbidden:  'jet', 'hsv', 'rainbow'
```

## Theme-adaptive Chrome (matplotlib mapping)

The pipeline runs each implementation twice: `ANYPLOT_THEME=light` → `plot-light.png`, `ANYPLOT_THEME=dark` → `plot-dark.png`. Backgrounds, text, grid, spines, legend frames, and annotation boxes all flip; only the Okabe-Ito data colors stay constant.

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED   = "#6B6A63" if THEME == "light" else "#A8A79F"

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.set_title(..., color=INK)
ax.set_xlabel(..., color=INK); ax.set_ylabel(..., color=INK)
ax.tick_params(colors=INK_SOFT, labelcolor=INK_SOFT)
for s in ('left', 'bottom'): ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.10, color=INK)

leg = ax.legend(...)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Annotations (sparingly, only when spec requests them)
ax.annotate(..., color=INK,
            bbox=dict(facecolor=ELEVATED_BG, edgecolor=INK_SOFT, alpha=0.9))

plt.savefig(f'plot-{THEME}.png', dpi=300, bbox_inches='tight', facecolor=PAGE_BG)
```

## Output Files

- Implementation file: `plots/{spec-id}/implementations/matplotlib.py` — single source, executed by the pipeline twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (matplotlib is PNG-only).
