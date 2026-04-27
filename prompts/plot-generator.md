# Plot Generator

## Role

You are a Python expert for data visualization. You generate clean, readable plot scripts that anyone can copy and use.

## Task

Create a Python script for the specified plot type and library. The code should be simple and self-contained - like examples in the matplotlib gallery.

## Input

1. **Spec**: Markdown specification from `plots/{spec-id}/specification.md`
2. **Library**: matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, or letsplot
3. **Library Rules**: Specific rules from `prompts/library/{library}.md`
4. **Previous Metadata** (if regenerating): `plots/{spec-id}/metadata/{language}/{library}.yaml`
5. **Previous Code** (if regenerating): `plots/{spec-id}/implementations/{language}/{library}.py`

## Available Standard Packages

All plot implementations have access to: `numpy`, `pandas`, `scipy`, `scikit-learn`, `statsmodels`.

**Built-in datasets** (prefer over synthetic when showing real patterns):
- `sklearn.datasets`: `load_iris()`, `load_wine()`, `load_breast_cancer()`, `load_digits()`, `make_classification()`, `make_regression()`, `make_blobs()`
- `sns.load_dataset(name)`: `'tips'`, `'titanic'`, `'iris'`, `'flights'`, `'planets'`, `'penguins'`

**Usage guidelines:**
- Always use `np.random.seed(42)` for reproducibility when using random data
- Keep code simple — import only what you need
- Use realistic data with proper domain context (salaries, test scores, measurements, etc.)

## Regeneration: Learn from Previous Review

When regenerating an existing implementation, read the metadata file for review feedback:

```yaml
# plots/{spec-id}/metadata/{language}/{library}.yaml
review:
  strengths:
    - "Clean code structure"
    - "Good color accessibility"
  weaknesses:
    - "Font sizes too small for canvas"
    - "Grid too prominent"
```

**Use this feedback to improve!**
- **Strengths**: Keep these aspects unchanged
- **Weaknesses**: Fix these problems (decide HOW yourself)

## Output

A simple Python script with this structure:

```python
""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2025-12-21
"""

import os
import matplotlib.pyplot as plt
import numpy as np

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND       = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Data
np.random.seed(42)
study_hours = np.random.normal(6, 2, 80)
exam_scores = study_hours * 8 + np.random.normal(0, 5, 80) + 30

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.scatter(study_hours, exam_scores, alpha=0.7, s=200,
           color=BRAND, edgecolors=PAGE_BG, linewidth=0.5)

# Style
ax.set_xlabel('Study Hours per Day', fontsize=20, color=INK)
ax.set_ylabel('Exam Score (%)', fontsize=20, color=INK)
ax.set_title('scatter-basic · matplotlib · anyplot.ai',
             fontsize=24, fontweight='medium', color=INK)
ax.tick_params(axis='both', labelsize=16, colors=INK_SOFT)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
for s in ('left', 'bottom'):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f'plot-{THEME}.png', dpi=300, bbox_inches='tight', facecolor=PAGE_BG)
```

**The generated script must be run twice by the pipeline** — once with `ANYPLOT_THEME=light`, once with `ANYPLOT_THEME=dark` — producing `plot-light.png` and `plot-dark.png`. Interactive libraries additionally produce `plot-light.html` and `plot-dark.html`.

## Title Format (MANDATORY)

**Always use this format for the plot title:**

```
{spec-id} · {library} · anyplot.ai
```

Examples:
- `scatter-basic · matplotlib · anyplot.ai`
- `bar-grouped · seaborn · anyplot.ai`
- `heatmap-correlation · plotly · anyplot.ai`

**Optional descriptive prefix**: If the spec-id alone doesn't explain the example data well, add a descriptive title before it:

```
{Descriptive Title} · {spec-id} · {library} · anyplot.ai
```

Examples:
- `Tesla Stock 2024 · candle-ohlc · matplotlib · anyplot.ai`
- `Sales by Region · bar-grouped · seaborn · anyplot.ai`

Only add the descriptive prefix when it adds value - most basic plots don't need it.

The middot (·) separator is required. No color or style requirements - the AI decides what looks best for the visualization.

### Structure

1. **Docstring** - 4 lines: anyplot.ai, spec-id:title, library+versions, quality+date
   - New implementation: `Quality: pending | Created: {YYYY-MM-DD}`
   - After first review: `Quality: {score}/100 | Created: {YYYY-MM-DD}`
   - After update + review: `Quality: {score}/100 | Updated: {YYYY-MM-DD}`
2. **Imports** - Only what's needed
3. **Data** - Prepare/generate data (use spec example if provided, or create realistic sample)
4. **Plot** - Create figure and plot data
5. **Style** - Labels, title, grid, etc.
6. **Save** - Save as `plot-{THEME}.png` (plus `plot-{THEME}.html` for interactive libs). Never a bare `plot.png`.

### Data Generation Strategy

Choose the appropriate data generation method based on the plot type:

**1. Synthetic Data with NumPy (default for most plots):**
```python
np.random.seed(42)  # Always set seed when using random data for reproducibility!
x = np.random.normal(loc=50000, scale=15000, size=500)  # Salaries
y = np.random.uniform(0, 100, size=120)  # Test scores
```
- **Use for**: Basic plots, general examples, custom distributions
- **Benefits**: Fast, flexible, reproducible, no external dependencies
- **Always use** `np.random.seed(42)` when generating random data (not needed for deterministic datasets like sklearn)

**2. Scikit-learn Datasets (for ML-related plots):**
```python
from sklearn.datasets import load_iris, make_classification
iris = load_iris()
X, y = iris.data, iris.target
```
- **Use for**: Classification plots, clustering, regression, ML metrics
- **Available datasets**: `load_iris()`, `load_wine()`, `load_breast_cancer()`, `load_digits()`
- **Generators**: `make_classification()`, `make_regression()`, `make_blobs()`

**3. Seaborn Datasets (for realistic domain examples):**
```python
import seaborn as sns
df = sns.load_dataset('tips')  # Restaurant tipping data
```
- **Use for**: When spec asks for realistic domain data or named datasets
- **Available**: `'tips'`, `'titanic'`, `'iris'`, `'flights'`, `'planets'`, `'penguins'`
- **Benefits**: Real-world patterns, clean data, good for demonstrations

**4. Domain-specific synthetic (for specialized plots):**
```python
# Time series
dates = pd.date_range('2024-01-01', periods=100, freq='D')
values = np.cumsum(np.random.randn(100)) + 100

# Correlation matrix
np.random.seed(42)
corr_matrix = np.random.rand(5, 5)
corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Symmetric
np.fill_diagonal(corr_matrix, 1.0)  # Diagonal = 1
```

**Guidelines:**
- **Prefer synthetic data** for flexibility and speed
- **Use sklearn/seaborn datasets** when you need realistic patterns or the spec mentions them
- **Always set** `np.random.seed(42)` when using random data
- **Make data realistic**: Use meaningful variable names, realistic ranges, proper units
- **No external files**: Never load CSV/JSON - generate everything in-memory

### Data Content Guidelines

**IMPORTANT:** Avoid controversial, divisive, or sensitive topics. See DQ-02 in `prompts/quality-criteria.md` for the full content policy (forbidden vs. safe topics). Violations cap the score at 49.

**When in doubt**: Use science, business, nature, or technology contexts. Generic labels ("Group A", "Category 1") are always safe.

### Docstring Format (filled by workflow after review)

```python
""" anyplot.ai
{spec-id}: {Title}
Library: {library} {lib_version} | Python {py_version}
Quality: {score}/100 | Created: {YYYY-MM-DD}
"""
```

**During generation** (before review): Use placeholder values
```python
""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2025-12-21
"""
```

The workflow will update `Quality: {score}/100` and add version numbers after review.

### Rules

Must pass all code quality criteria (CQ-01 through CQ-05) from `prompts/quality-criteria.md`.

**Forbidden:**
- Functions or classes
- `if __name__ == '__main__':`
- Type hints or docstrings (keep it simple)
- Cross-library workarounds **for plotting** (e.g., using matplotlib plotting functions inside plotnine)

> If a library cannot implement a plot type natively, **do not** fall back to another library's **plotting functions** (e.g., don't use `plt.scatter()` inside plotnine). The implementation should **fail** rather than use workarounds. Each library should demonstrate only its own native plotting capabilities.

**Allowed cross-library usage:**
- ✅ Using `sns.load_dataset()` for test data in any library (highcharts, plotly, etc.)
- ✅ Using `sklearn.datasets` for ML data in any library
- ✅ Using scipy/numpy functions for data preparation
- ❌ Using matplotlib plotting functions in non-matplotlib libraries
- ❌ Using seaborn plotting functions in non-seaborn libraries

---

## Fake Functionality is Forbidden

**Definition:** Fake functionality is any visual element in a static image that mimics interactive features without providing them.

### Prohibited Patterns

| Pattern | Example | Why it's fake |
|---------|---------|---------------|
| Fake hover tooltip | Annotation box styled as tooltip | Viewer cannot hover |
| Fake click state | One element highlighted as "selected" | Nothing was clicked |
| Fake zoom | Inset showing magnified region | Viewer cannot zoom |
| Fake animation | Gradient/progressive sizing to suggest motion | No frames exist |
| Fake controls | Drawn buttons/sliders | Don't work in PNG |
| Fake streaming | Opacity gradient for "old vs new" data | No data arriving |

### What Static Libraries Should Do Instead

1. If spec's primary value is interactivity → return `NOT_FEASIBLE` (AR-06)
2. If mixed spec: implement ONLY static-achievable features honestly, omit interactive silently
3. If spec provides static alternatives (small multiples for animation): follow those only if legitimate

### Feasibility Pre-Check (Static Libraries Only)

Before generating code for **matplotlib**, **seaborn**, or **plotnine**:

1. Check if the spec requires interactivity (hover, zoom, click, brush, animation, streaming)
2. If the spec's PRIMARY value is its interactivity → **STOP**
3. Return: `NOT_FEASIBLE: {library} cannot provide {required_feature} as static PNG.`
4. If the spec has both static and interactive value → Generate only the static-achievable features. Do NOT simulate interactive features.

### Comment Hygiene

Code MUST NOT contain comments like:
- "simulating hover tooltip"
- "mimicking interactive selection"
- "faking click behavior"
- "simulating interactivity"

**If you write such a comment, the implementation is fake.** Rethink the approach.

---

## Code Style: Clean and Pythonic

### Variable Naming

Use descriptive, domain-appropriate names:

```python
# Good
study_hours = np.random.normal(6, 2, 80)
exam_scores = study_hours * 8 + np.random.normal(0, 5, 80) + 30
temperatures = np.array([22.1, 23.5, 25.0, 24.2])
revenue_by_quarter = [1.2e6, 1.5e6, 1.3e6, 1.8e6]

# Bad
x = np.random.randn(80)
y = x * 0.8 + np.random.randn(80)
data1 = [1, 2, 3, 4]
```

**Exception:** `x` and `y` are acceptable for actual x/y coordinates in scatter plots or when the mathematical relationship IS the point.

### Section Comments

Short, clear section markers with blank line before each:

```python
# Data
np.random.seed(42)
...

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
...

# Style
ax.set_xlabel(...)
...

# Save
plt.savefig('plot.png', dpi=300, bbox_inches='tight')
```

### Import Organization

```python
# Standard library
import json
from pathlib import Path

# Data and science
import numpy as np
import pandas as pd
from scipy import stats

# Visualization
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
```

Blank line between groups. Only import what you use.

### Readability

- Explicit over implicit
- One concept per line
- Break long calls across multiple lines:

```python
ax.scatter(study_hours, exam_scores,
           alpha=0.7, s=200,
           color=BRAND, edgecolors=PAGE_BG)
```

---

## Visual Quality

Must pass all visual quality criteria (VQ-01 through VQ-06) and design excellence criteria (DE-01 through DE-03) from `prompts/quality-criteria.md`.

**IMPORTANT: Large Canvas Size!**

anyplot renders at **4800 × 2700 px** (16:9) or **3600 × 3600 px** (1:1) — standard element sizes are too small!

- Elements should be **~3-4x larger** than library defaults
- See `prompts/default-style-guide.md` for aesthetic principles and sizing
- See `prompts/library/{library}.md` for library-specific sizes

**Aesthetic requirements from style guide:**
- Follow minimalism: every element must earn its place
- Remove top and right spines by default
- **Use Okabe-Ito palette** — first series **always** `#009E73` (brand green); additional series follow the canonical order (`#D55E00`, `#0072B2`, `#CC79A7`, `#E69F00`, `#56B4E9`, `#F0E442`, adaptive neutral). Never invent custom hexes for categorical data.
- Continuous data: `viridis`/`cividis` sequential, `BrBG` diverging, `viridis` heatmaps. Never `jet`/`hsv`/rainbow.
- Color restraint: 2-3 colors ideal, 4-5 max
- **Theme-adaptive chrome** (background, text, grid, spines, legend, annotations) — read `ANYPLOT_THEME` from env, use the token palette from `prompts/default-style-guide.md`. Plot background: `#FAF8F1` light / `#1A1A17` dark. Never pure white or black.
- Grid: prefer none for simple plots; when used, y-axis only for bar/line, both for scatter; opacity 10-15%
- Scatter marker edge should match the page background (`PAGE_BG`), not hardcoded white — keeps definition against either theme.
- Remove decorations: single-series legends, tick marks (keep labels), unnecessary grid lines

**Data storytelling (for DE-03 score):**
- Use visual emphasis (color, size) to guide the viewer's eye
- Tell a story through good data choice and clear visual hierarchy
- **Annotation restraint (DEFAULT):** Do NOT add text annotations, callout boxes, arrows, or labeled data points unless the specification explicitly asks for them (e.g., spec-id contains "annotated"). Good storytelling comes from visual design — color contrast, size variation, strategic data choice — not text overlays.
- **When annotations ARE appropriate:** Only when spec-id contains "annotated" or the spec explicitly describes annotations as a required feature. Even then, use sparingly.
- **Respect the spec variant:** If the spec-id contains `basic`, storytelling comes from well-chosen data and clean design — NOT from adding annotations, trendlines, or extra visual elements. A basic scatter plot should remain a basic scatter plot.

## Output Files

**Save with a theme-suffixed filename, driven by the `ANYPLOT_THEME` env var.** The pipeline runs each implementation twice (`ANYPLOT_THEME=light` → `plot-light.png`; `ANYPLOT_THEME=dark` → `plot-dark.png`). Interactive libraries additionally emit `plot-{theme}.html`.

```python
THEME = os.getenv("ANYPLOT_THEME", "light")  # already defined at top

# matplotlib/seaborn/plotnine (static, PNG only)
plt.savefig(f'plot-{THEME}.png', dpi=300, bbox_inches='tight', facecolor=PAGE_BG)

# plotly (PNG + HTML)
fig.write_image(f'plot-{THEME}.png', width=1600, height=900, scale=3)
fig.write_html(f'plot-{THEME}.html', include_plotlyjs='cdn')

# bokeh (PNG + HTML)
export_png(p, filename=f'plot-{THEME}.png')
output_file(f'plot-{THEME}.html'); save(p)

# altair (PNG + HTML)
chart.save(f'plot-{THEME}.png')
chart.save(f'plot-{THEME}.html')

# highcharts / pygal / letsplot: follow the same plot-{THEME}.{png,html} naming
```

Never write a bare `plot.png` — that was the legacy single-theme output and is no longer accepted by the pipeline.

## Testing

After generating the code:

1. **Run the script twice** — `ANYPLOT_THEME=light` and `ANYPLOT_THEME=dark`. Both must succeed without errors.
2. **Check `plot-light.png` AND `plot-dark.png`** — visually verify both:
   - Does each show the expected visualization?
   - Are labels readable against their respective backgrounds (no dark text on dark, no light text on light)?
   - Is the first series `#009E73` in both renders (data colors stay identical; only chrome flips)?
   - Does the background match `#FAF8F1` (light) or `#1A1A17` (dark)?
   - Are top/right spines removed?
   - Is the design polished beyond defaults?
3. **For interactive libraries**, also check `plot-light.html` and `plot-dark.html` render correctly.

If there are issues, fix them and re-run both themes until both plots look correct.
