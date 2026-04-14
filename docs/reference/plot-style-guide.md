# Plot Style Guide

The visual language for every plot in **anyplot.ai** — what colors to use, why they were chosen, and how to apply them consistently across nine Python plotting libraries.

## TL;DR

We use the **Okabe-Ito** 8-color categorical palette, peer-reviewed for colorblind safety, with **Bluish Green `#009E73`** as the brand anchor. The palette works identically on light and dark backgrounds because the eighth slot (`neutral`) is adaptive: `#1A1A1A` on light, `#E8E8E0` on dark.

```python
anyplot_palette = [
    "#009E73",  # 01 · bluish green   ★ brand
    "#D55E00",  # 02 · vermillion
    "#0072B2",  # 03 · blue
    "#CC79A7",  # 04 · reddish purple
    "#E69F00",  # 05 · orange
    "#56B4E9",  # 06 · sky blue
    "#F0E442",  # 07 · yellow
    # 08 · neutral — adaptive: #1A1A1A on light, #E8E8E0 on dark
]
```

## Why Okabe-Ito?

The Okabe-Ito palette was published in 2008 by Masataka Okabe (Jikei Medical School) and Kei Ito (University of Tokyo) as part of their research on accessible color design for scientific figures. It was optimized empirically for three types of color vision deficiency (CVD) — deuteranopia, protanopia, and tritanopia — which together affect roughly 8% of men and 0.5% of women of Northern European descent.

Three properties make it the right choice for a multi-library plotting catalogue:

**It's peer-reviewed and widely trusted.** ggplot2, seaborn, and many scientific R/Python toolkits offer it as a built-in option. Using it means our examples are immediately credible in academic and publication contexts.

**It's stable across backgrounds.** Every color has enough luminance contrast to remain distinguishable on both white and near-black backgrounds. This matters for documentation sites, notebooks, and embedded plots alike.

**Eight colors is the right cap.** Research by Ware, Glasbey, and Miller on distinguishable categorical colors converges on 7 ± 2 as the practical limit before viewers start confusing categories. Eight is the ceiling, and Okabe-Ito sits exactly there.

## The Colors

| # | Role          | Hex        | Semantic Use                                                  |
|---|---------------|------------|---------------------------------------------------------------|
| 1 | Brand         | `#009E73`  | Logo dot, first category in any plot, primary CTAs            |
| 2 | Secondary     | `#D55E00`  | Second category, warm contrast, warnings                      |
| 3 | Tertiary      | `#0072B2`  | Third category, cool anchor, informational links              |
| 4 | Quaternary    | `#CC79A7`  | Fourth category, soft, distinctive                            |
| 5 | Accent warm   | `#E69F00`  | Fifth category, highlights, hover states                      |
| 6 | Accent cool   | `#56B4E9`  | Sixth category, info states, secondary links                  |
| 7 | Highlight     | `#F0E442`  | Seventh category — use sparingly, poor on white backgrounds   |
| 8 | Neutral       | adaptive   | Text, gridlines, "other", totals                              |

### The adaptive neutral

Position 8 is not a fixed color but a **role** that switches based on the theme:

- **Light theme** → `#1A1A1A` (near-black, softer than pure `#000`)
- **Dark theme** → `#E8E8E0` (near-white, softer than pure `#FFF`)

This follows the `semantic tokens` pattern used in Apple HIG, Material Design, and GitHub Primer. The first seven colors stay identical across themes so that a category retains its identity; only the neutral flips.

Pure black on pure white is visually too harsh and increases eye strain. The slight desaturation on both ends of the neutral improves legibility for extended reading without sacrificing contrast ratio.

## Order matters

The color order is **not wissenschaftlich prescribed** — the Okabe-Ito paper lists the colors but doesn't mandate a sequence. We've chosen an order optimized for two goals:

1. **Brand consistency.** Position 1 is always `#009E73`. The first data series in every plot is automatically our brand color, which links the plot visually to the logo and the rest of the site.

2. **Maximum early contrast.** Positions 1–4 alternate between warm and cool, saturated hues to guarantee maximum distinguishability for plots with few categories (the common case). Orange (`#E69F00`) and Yellow (`#F0E442`) — which share the yellow-orange region and look similar side-by-side — are separated by four positions. Black/neutral sits last, reserved for the residual "other" category.

```
green → vermillion → blue → purple → orange → sky → yellow → neutral
warm?   warm         cool    warm     warm      cool   warm    neutral
sat.    sat.         sat.    sat.     sat.      soft   soft
```

For plots with 2–4 categories, you get a clean green/orange/blue/purple palette. For 5+ categories, the remaining colors fill in without ambiguity.

## Usage rules

### Plot defaults

- **First series = brand color (`#009E73`)**. Always. This is the single most important consistency rule.
- **Neutral (position 8) is reserved** for aggregates, residuals, and reference lines. Don't use it for a normal category unless you've exhausted the other seven.
- **Yellow (`#F0E442`) on white backgrounds** has poor contrast. Use it only for position 7 or later, never for thin lines or small markers.

### Mixing with UI

The palette is shared between plots and UI, but UI uses only a restricted subset:

- `#009E73` for brand elements, primary CTAs, active nav states, success messages
- `#D55E00` for error states, destructive actions
- `#E69F00` for "new" badges, info highlights
- `#0072B2` for informational links, footnotes

Positions 4, 6, and 7 (Purple, Sky, Yellow) are **plot-only**. Keeping them out of the UI reserves their visual impact for the moment a user encounters a visualization.

### Non-categorical data

Okabe-Ito is a **categorical** palette — it's for distinct categories, not ordered or continuous data. For other data types:

- **Sequential (single-variable magnitude)**: use `viridis` or `cividis`. Both are perceptually uniform and colorblind-safe. `cividis` is additionally optimized for print.
- **Diverging (two-sided, midpoint-anchored)**: use `BrBG` (brown-to-bluish-green) from ColorBrewer, or construct one centered on a neutral tone.
- **Heatmaps**: use `viridis` for general-purpose, `Reds`/`Blues` for single-polarity intensity.

Don't reach for Okabe-Ito for these cases — a categorical palette on continuous data produces misleading banding artifacts.

## Validation

Every palette change should be validated against:

- **Deuteranopia** (red-green confusion, most common CVD, ~6% of men)
- **Protanopia** (red-weak, ~1% of men)
- **Tritanopia** (blue-yellow confusion, rare but important)

Recommended tools:

- [Viz Palette](https://projects.susielu.com/viz-palette) — interactive CVD simulator for palettes
- [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/) — upload a plot image, see all three simulations
- [Sim Daltonism](https://michelf.ca/projects/sim-daltonism/) — macOS system-wide CVD simulator
- [Colour Science for Python](https://www.colour-science.org/) — programmatic access to Machado et al. (2009) simulation matrices

For algorithmic palette generation beyond Okabe-Ito, see Petroff (2021) — a more recent palette optimized with numerical solvers in the CAM02-UCS perceptual color space.

## Background surfaces

Plots sit inside **surface containers** with consistent styling:

| Surface     | Light          | Dark           | Use                         |
|-------------|----------------|----------------|-----------------------------|
| `page`      | `#FFFFFF`      | `#121210`      | Outer page background       |
| `surface`   | `#FAFAF6`      | `#1A1A17`      | Cards, plot containers      |
| `elevated`  | `#FFFFFF`      | `#242420`      | Modals, tooltips            |

Plot containers use `surface` with a 1px border (`rgba(0,0,0,0.08)` on light, `rgba(255,255,255,0.08)` on dark) and 12–24px border-radius depending on context. The subtle elevation differentiates plots from page content without harsh boundaries.

## Typography in plots

- **Tick labels, legends, annotations**: MonoLisa or fallback monospace, 10–12px
- **Axis labels**: MonoLisa, 11–13px, `gray-600` (`#4b5563`)
- **Plot titles**: MonoLisa, 13–15px, `gray-800` (`#1f2937`), rendered outside the plot in the container header rather than inside the axes

Monospace throughout keeps plots consistent with the code-forward brand and aligns with how readers see plot labels in Jupyter notebooks and documentation.

## Implementation reference

The palette is exposed in the Python library as:

```python
import anyplot as ap

# full palette as list
ap.palettes.okabe_ito              # returns list of 8 hex strings

# by role name
ap.palettes.okabe_ito.brand        # "#009E73"
ap.palettes.okabe_ito.vermillion   # "#D55E00"
ap.palettes.okabe_ito.blue         # "#0072B2"
# ...

# theme-aware neutral
ap.palettes.okabe_ito.neutral("light")   # "#1A1A1A"
ap.palettes.okabe_ito.neutral("dark")    # "#E8E8E0"

# as matplotlib cycler
import matplotlib.pyplot as plt
plt.rcParams['axes.prop_cycle'] = ap.palettes.okabe_ito.cycler()
```

For CSS:

```css
:root {
  --ap-green:      #009E73;
  --ap-vermillion: #D55E00;
  --ap-blue:       #0072B2;
  --ap-purple:     #CC79A7;
  --ap-orange:     #E69F00;
  --ap-sky:        #56B4E9;
  --ap-yellow:     #F0E442;
  --ap-neutral:    #1A1A1A;  /* adaptive */
}

@media (prefers-color-scheme: dark) {
  :root { --ap-neutral: #E8E8E0; }
}
```

## References

1. Okabe, M. & Ito, K. (2008). *Color Universal Design (CUD): How to make figures and presentations that are friendly to colorblind people.* Jikei Medical School / University of Tokyo. [https://jfly.uni-koeln.de/color/](https://jfly.uni-koeln.de/color/)

2. Wong, B. (2011). *Points of view: Color blindness.* Nature Methods 8, 441. [https://doi.org/10.1038/nmeth.1618](https://doi.org/10.1038/nmeth.1618) — extends Okabe-Ito with publication-specific usage guidelines.

3. Machado, G. M., Oliveira, M. M. & Fernandes, L. A. F. (2009). *A physiologically-based model for simulation of color vision deficiency.* IEEE Transactions on Visualization and Computer Graphics 15(6), 1291–1298. — the simulation model used by most modern CVD validators.

4. Petroff, M. A. (2021). *Accessible Color Sequences for Data Visualization.* arXiv:2107.02270. — modern alternative using CAM02-UCS optimization; relevant if green is not a required anchor.

5. Brewer, C. A. (2003). *ColorBrewer in Print: A Catalog of Color Schemes for Maps.* Cartography and Geographic Information Science 30(1). [https://colorbrewer2.org](https://colorbrewer2.org) — the gold standard for cartographic color schemes, useful for reference beyond categorical palettes.

6. van der Walt, S. & Smith, N. (2015). *A Better Default Colormap for Matplotlib.* SciPy 2015. — the paper behind `viridis`, the recommended sequential colormap.

---

*Last updated: 2026. Maintained alongside the anyplot.ai code catalogue.*
