# Quality Criteria

Two-stage evaluation: Auto-Reject + Quality Scoring.

## Overview

```text
Implementation
     │
     ▼
┌─────────────────────┐
│  Stage 1: Auto-Reject  │  ──► FAIL → Score = 0, regenerate
│  (8 quick checks)      │
└─────────────────────┘
     │ PASS
     ▼
┌─────────────────────┐
│  Stage 2: Quality      │  ──► ≥ 90 → ai-approved, merge
│  (0-100 points)        │  ──► < 90 → ai-rejected, repair (max 3x)
└─────────────────────┘
     │ After 3 attempts
     ▼
┌─────────────────────┐
│  Final Decision        │  ──► ≥ 50 → merge to repo
│                        │  ──► < 50 → not in repo, regenerate
└─────────────────────┘
```

---

## Stage 1: Auto-Reject

Quick checks **before** AI evaluation. On fail: Score=0, no retry.

| ID | Check | Description | Verification |
|----|-------|-------------|--------------|
| AR-01 | SYNTAX_ERROR | Code cannot be parsed | `python -m py_compile` |
| AR-02 | RUNTIME_ERROR | Code throws exception | Execution with timeout |
| AR-03 | NO_OUTPUT | No `plot.png` created | File exists? |
| AR-04 | EMPTY_PLOT | Image empty | < 10KB or > 95% white |
| AR-05 | NO_LIBRARY | Library not used | 0 plot functions from library |
| AR-06 | NOT_FEASIBLE | Library cannot implement spec | AI decision |
| AR-07 | WRONG_FORMAT | Wrong output type | Not .png for static libraries |
| AR-08 | FAKE_FUNCTIONALITY | Static library simulates interactive features | AI decision |

**Check order:** AR-01 → AR-02 → AR-03 → AR-04 → AR-05 → AR-06 → AR-07 → AR-08

### AR-05: Library Usage

Implementation must use **plot functions** from the library, not just styling.

| Library | Must use | NOT sufficient |
|---------|----------|----------------|
| seaborn | `sns.scatterplot`, `sns.barplot`, `sns.heatmap`, etc. | Only `sns.set_style()` or `sns.load_dataset()` |
| plotly | `px.*` or `go.*` plot functions | Only `update_layout()` |
| bokeh | `figure.scatter()`, `figure.line()`, etc. | Only styling |
| altair | `alt.Chart().mark_*()` | Only `configure_*()` |
| plotnine | `ggplot() + geom_*()` | Only `theme()` |
| pygal | Chart classes with data | Only config |
| highcharts | Chart with series | Only options |
| letsplot | `ggplot() + geom_*()` | Only `ggsize()` |

**Note:** Using data loading utilities (e.g., `sns.load_dataset()`, `sklearn.datasets`) from other libraries is allowed and does not count as library usage. This check only evaluates whether the implementation uses the library's **plotting functions**.

### AR-06: Not Feasible

When a library cannot technically implement a spec (e.g., pygal cannot do 3D), this is an Auto-Reject. No retry, no file in repo.

### AR-08: Fake Functionality

A static library (matplotlib, seaborn, plotnine) simulates interactive features that cannot work in a PNG image.

**Triggers (auto-reject):**
- Simulated tooltips (annotation boxes styled to look like hover tooltips)
- Simulated selection/hover state (one element highlighted as if "clicked" or "hovered")
- Simulated UI controls (drawn buttons, sliders, dropdown menus)
- Code comments containing "simulating hover", "simulating click", "simulating interactivity", or similar

**NOT auto-reject (legitimate techniques):**
- Small multiples / faceted grids as static alternative to animation
- Cell annotations in heatmaps (these are native text, not fake tooltips)
- Color encoding of time direction (arrows, gradients showing progression)
- Honest notes like "See Plotly version for interactive features"

---

## Allowed Image Formats

| Format | Size | Aspect Ratio |
|--------|------|--------------|
| **Landscape** | 4800 × 2700 px | 16:9 |
| **Square** | 3600 × 3600 px | 1:1 |

**Both have ~13M pixels** → same font sizes work for both.

**AI decides freely** which format is best for the specific plot.

---

## Stage 2: Quality Scoring (100 Points)

**Only if Stage 1 passed.** Focus purely on quality.

### Scoring Philosophy: STRICT

| Score | Tier | Outcome |
|-------|------|---------|
| 90-100 | Excellent | **Approved immediately** - Publication quality |
| 70-89 | Good | Repair loop → merge after 3 attempts |
| 50-69 | Acceptable | Repair loop → merge after 3 attempts |
| < 50 | Poor | Repair loop → **NOT in repo** after 3 attempts |

**Workflow:**
- **≥ 90**: ai-approved, merged immediately
- **< 90**: ai-rejected, repair loop (up to 3 attempts)
- **After 3 attempts**: ≥ 50 → merge, < 50 → close PR and regenerate

**Principles:**
- Full points only for **perfect** implementation
- Small flaws = immediate deduction
- "Good enough" = maximum 70%
- 90%+ = could appear in Nature/Science

### Point Distribution

| Category | Points | Focus |
|----------|--------|-------|
| Visual Quality | 30 | Readability, clarity, no defects |
| Design Excellence | 20 | Aesthetic sophistication, storytelling, polish |
| Spec Compliance | 15 | Matches the spec? |
| Data Quality | 15 | Good example data? |
| Code Quality | 10 | Clean code? |
| Library Mastery | 10 | Uses library strengths creatively? |
| **Total** | **100** | |

---

## Visual Quality (30 Points)

| ID | Criterion | Max | Scoring |
|----|-----------|-----|---------|
| VQ-01 | Text Legibility | 8 | 8=perfect (sizes explicitly set), 5=good, 3=ok, 0=poor |
| VQ-02 | No Overlap | 6 | 6=no overlap, 3=minimal, 0=overlap |
| VQ-03 | Element Visibility | 6 | 6=optimal sizing, 3=visible, 0=barely visible |
| VQ-04 | Color Accessibility | 4 | 4=perfect colorblind-safe, 2=ok, 0=red-green |
| VQ-05 | Layout & Canvas | 4 | 4=perfect, 2=ok, 0=cut-off |
| VQ-06 | Axis Labels & Title | 2 | 2=with units, 1=descriptive, 0=x/y |

### VQ-01: Text Legibility (8 Points)

All text must be clearly readable at 4800×2700 / 3600×3600 px.

| Points | Criterion |
|--------|-----------|
| 8 | All font sizes explicitly set: Title ≥24pt, Labels ≥20pt, Ticks ≥16pt, all perfectly readable |
| 5 | All readable, but relying on library defaults rather than explicit sizing |
| 3 | Partially too small |
| 0 | Text hard to read |

**Key distinction:** Score of 8 requires **explicitly setting** font sizes, not just lucky defaults.

### VQ-02: No Overlap (6 Points)

No overlapping text elements.

| Points | Criterion |
|--------|-----------|
| 6 | No overlap - all text fully readable |
| 3 | Minimal overlap, main content readable |
| 0 | Significant overlap, text unreadable |

**Common problems:**
- X-axis labels overlap with many categories
- Tick labels overlap each other
- Legend overlaps data

### VQ-03: Element Visibility (6 Points)

Data elements must be visible and adapted to data density.

| Points | Criterion |
|--------|-----------|
| 6 | Markers/lines perfectly adapted to data density |
| 3 | Visible, but not optimal (too big/small) |
| 0 | Elements barely visible or completely overlapping |

**Guidelines for Scatter:**

| Data points | Marker Size (s=) | Alpha |
|-------------|------------------|-------|
| < 30 | 200-400 | 0.9-1.0 |
| 30-100 | 100-200 | 0.7-0.9 |
| 100-300 | 50-100 | 0.5-0.7 |
| 300+ | 20-50 | 0.3-0.5 |

### VQ-04: Color Accessibility (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | Perfect colorblind-safe, good contrast |
| 2 | Acceptable, but not optimal |
| 0 | Red-green as only difference |

**Recommended palettes:** `viridis`, `colorblind`, `tab10`

### VQ-05: Layout Balance & Canvas Utilization (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | Perfect layout: plot fills 50-80% of canvas, balanced margins |
| 2 | Minor issues: plot fills 30-50% of canvas, some wasted space |
| 0 | **Severe**: plot fills <30% of canvas, OR content cut-off, OR legend isolated |

**Canvas Utilization Rules:**
- Plot elements (chart, axes, labels) should use **at least 40%** of the canvas area
- Whitespace should be **balanced** around the plot (not all on one side)
- Legend should be **near** the plot, not floating isolated in empty space
- Tiny plot in center of huge canvas = **automatic 0 points**

### VQ-06: Axis Labels & Title (2 Points)

| Points | Criterion |
|--------|-----------|
| 2 | Descriptive with units: "Temperature (°C)" |
| 1 | Descriptive without units: "Temperature" |
| 0 | Generic: "x", "y", or empty |

---

## Design Excellence (20 Points)

This category evaluates aesthetic sophistication beyond mere correctness. A plot can be technically correct but visually generic — Design Excellence separates "works" from "beautiful."

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| DE-01 | Aesthetic Sophistication | 8 | Color harmony, typography, professional polish |
| DE-02 | Visual Refinement | 6 | Grid styling, whitespace, attention to detail |
| DE-03 | Data Storytelling | 6 | Visual hierarchy, data choice, emphasis on insight |

### DE-01: Aesthetic Sophistication (8 Points)

| Points | Criterion |
|--------|-----------|
| 8 | Publication-ready: custom palette, intentional hierarchy, FiveThirtyEight-level design |
| 6 | Strong design: thoughtful colors, good typography, clearly above defaults |
| 4 | Looks like a well-configured library default |
| 2 | Generic/boring: default colors, no design thought |
| 0 | Ugly: clashing colors, poor typography, looks broken |

**Calibration:** DE-01 > 6 is rare on first attempt. Most implementations will score 2-4.

### DE-02: Visual Refinement (6 Points)

| Points | Criterion |
|--------|-----------|
| 6 | Perfect: subtle grid (or none), spines removed, generous whitespace, every detail polished |
| 4 | Good: some refinement visible (grid adjusted, spines partially removed) |
| 2 | Default: library defaults with minimal customization |
| 0 | Sloppy: bold grid, all spines, cramped layout |

### DE-03: Data Storytelling (6 Points)

| Points | Criterion |
|--------|-----------|
| 6 | Excellent: plot tells a clear story through data choice, visual hierarchy, and emphasis — viewer immediately sees the insight |
| 4 | Good: visual hierarchy guides the reader — color contrast, size variation, or focal points create emphasis |
| 2 | Default: data is displayed but not interpreted — viewer must find their own story |
| 0 | None: raw data dump with no context |

**Calibration:** DE-03 = 2 is the default. Most implementations just display data without storytelling. Score of 4+ does NOT require annotations — visual hierarchy (color contrast, size variation, focal points) is sufficient. Annotations are only expected when the spec explicitly requests them (e.g., spec-id contains "annotated").

---

## Spec Compliance (15 Points)

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| SC-01 | Plot Type | 5 | Correct chart type |
| SC-02 | Required Features | 4 | All spec features present |
| SC-03 | Data Mapping | 3 | X/Y correctly assigned |
| SC-04 | Title & Legend | 3 | Title format correct, legend labels match data |

### SC-01: Plot Type (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Correct chart type, all subtypes present |
| 3 | Correct base type but missing variant (e.g., grouped bar instead of stacked) |
| 0 | Wrong chart type entirely |

### SC-02: Required Features (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | All features from spec present and working |
| 2 | Most features present, minor omissions |
| 0 | Key features missing |

### SC-03: Data Mapping (3 Points)

| Points | Criterion |
|--------|-----------|
| 3 | X/Y correctly assigned, axes show all data |
| 1 | Minor mapping issues |
| 0 | X/Y swapped or data not visible |

### SC-04: Title & Legend (3 Points)

| Points | Criterion |
|--------|-----------|
| 3 | Title format `{spec-id} · {library} · anyplot.ai` AND legend labels correct |
| 2 | Title format correct but legend issues, or vice versa |
| 1 | Partially correct |
| 0 | Missing or wrong |

---

## Data Quality (15 Points)

| ID | Criterion | Max | Scoring |
|----|-----------|-----|---------|
| DQ-01 | Feature Coverage | 6 | 6=shows ALL aspects, 3=most, 0=one-sided |
| DQ-02 | Realistic Context | 5 | 5=real scenario, 3=plausible, 1=abstract labels, 0=nonsense |
| DQ-03 | Appropriate Scale | 4 | 4=perfect values, 2=ok, 0=impossible |

### DQ-01: Feature Coverage (6 Points)

Example data must show ALL features of the plot type.

| Points | Criterion |
|--------|-----------|
| 6 | Shows all aspects (e.g., boxplot with outliers AND different distributions) |
| 3 | Shows main features, but not all edge cases |
| 0 | All groups look the same, no variation |

**Examples:**
- Candlestick: Bullish AND bearish candles
- Boxplot: Outliers AND different spreads
- Histogram: Multimodal distribution when appropriate

### DQ-02: Realistic Context (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Real, comprehensible, **neutral** scenario (science, business, nature) |
| 3 | Plausible, but generic |
| 1 | Abstract labels only ("Category A", "Group 1", "Series X") |
| 0 | Nonsensical data OR controversial/sensitive topic (politics, race, religion, gender stereotypes) |

**Content Policy:** Data must avoid controversial, divisive, or sensitive topics:
- ❌ Politics (elections, parties, voting)
- ❌ Religion, race/ethnicity comparisons
- ❌ Gender/sexuality stereotypes
- ❌ Violence, war, weapons
- ✅ Science, business, nature, technology, food, education (generic)

### DQ-03: Appropriate Scale (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | Perfect, realistic values for the context |
| 2 | Acceptable |
| 0 | Impossible values (temperatures of 500°C for weather) |

---

## Code Quality (10 Points)

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| CQ-01 | KISS Structure | 3 | Imports → Data → Plot → Save (no functions/classes) |
| CQ-02 | Reproducibility | 2 | `np.random.seed(42)` or deterministic data |
| CQ-03 | Clean Imports | 2 | Only used imports (including data utilities like `sns.load_dataset()`) |
| CQ-04 | Code Elegance | 2 | Appropriate complexity, no over-engineering, no fake functionality |
| CQ-05 | Output & API | 1 | Saves as `plot.png`, no deprecated functions |

### CQ-04: Code Elegance (2 Points)

| Points | Criterion |
|--------|-----------|
| 2 | Clean, Pythonic, appropriate complexity for the visualization |
| 1 | Acceptable but could be cleaner (e.g., overly verbose, duplicated logic) |
| 0 | Over-engineered, draws fake UI elements, or contains fake-functionality code/comments |

**CQ-04 = 0 if code draws fake interactive elements** (buttons, sliders, tooltip boxes) or contains comments like "simulating hover/click."

---

## Library Mastery (10 Points)

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| LM-01 | Idiomatic Usage | 5 | Uses library's recommended patterns and high-level API |
| LM-02 | Distinctive Features | 5 | Leverages features unique to this library |

### LM-01: Idiomatic Usage (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Expertly uses the library's high-level API and recommended patterns |
| 3 | Correct usage but doesn't leverage the library's best patterns |
| 1 | Minimal library usage, mostly manual/low-level code |

### LM-02: Distinctive Features (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Uses a feature that couldn't easily be replicated in another library |
| 3 | Uses some library-specific features |
| 1 | Generic usage — could be any library with minor syntax changes |

**Calibration:** LM-02 = 1 is the default. To score 3+, the implementation must use a feature distinctive to this specific library.

**Note:** Basic library usage is checked by AR-05. Library Mastery evaluates *quality* of usage.

---

## Score Caps

Certain errors limit the maximum score:

| Problem | Max Score |
|---------|-----------|
| VQ-02 = 0 (severe overlap) | 49 |
| VQ-03 = 0 (invisible elements) | 49 |
| SC-01 = 0 (wrong plot type) | 40 |
| DQ-02 = 0 (controversial/sensitive data) | 49 |
| **DE-01 ≤ 2 AND DE-02 ≤ 2** (generic + no visual refinement) | **75** |
| **CQ-04 = 0** (fake functionality / gross over-engineering) | **70** |

**The "correct but boring" cap:** A technically correct but visually generic plot (DE-01 ≤ 2) with no visual refinement (DE-02 ≤ 2) is capped at 75. This means it cannot pass on first review, even with perfect scores elsewhere. The repair loop will push it to improve aesthetic design and visual polish.

---

## Anti-Inflation Calibration Anchors

Evaluators must use these anchors to prevent score inflation:

- **Median implementation should score 72-78** — not 90+
- **DE-01 > 6 is rare** on first attempt — most plots look like configured defaults (score 4)
- **DE-02 = 2 is the default** — library defaults with minimal customization
- **DE-03 = 2 is the default** — most plots just display data without visual hierarchy or emphasis
- **LM-01 = 3 is the default** — correct usage but doesn't leverage the library's best patterns
- **LM-02 = 1 is the default** — most implementations use the library generically
- **When in doubt, deduct** — the repair loop exists to improve quality
- A plot scoring 90+ should genuinely impress a data visualization professional

**Expected distribution:**
- ~25-30% score 85+ on first attempt (vs. current ~95% scoring 90+)
- ~50-60% score 72-84 (good but need design/storytelling improvements)
- ~10-15% score below 72 (significant issues)

---

## Example Evaluation

A "good" plot (~76%):

```text
VISUAL QUALITY (24/30)
  VQ-01: 5/8   (readable, but relying on defaults not explicit sizes)
  VQ-02: 6/6   (no overlap)
  VQ-03: 5/6   (visible, markers could be better)
  VQ-04: 4/4   (good colors)
  VQ-05: 2/4   (ok layout, some wasted space)
  VQ-06: 2/2   (labels with units)

DESIGN EXCELLENCE (8/20)
  DE-01: 4/8   (well-configured default, not exceptional)
  DE-02: 2/6   (library defaults, minimal refinement)
  DE-03: 2/6   (data displayed but no storytelling)

SPEC COMPLIANCE (13/15)
  SC-01: 5/5   (correct type)
  SC-02: 3/4   (one minor feature missing)
  SC-03: 3/3   (mapping ok)
  SC-04: 2/3   (title ok, legend not perfect)

DATA QUALITY (13/15)
  DQ-01: 5/6   (shows most features)
  DQ-02: 4/5   (plausible scenario, not abstract)
  DQ-03: 4/4   (good values)

CODE QUALITY (9/10)
  CQ-01: 3/3   (KISS)
  CQ-02: 2/2   (seed set)
  CQ-03: 2/2   (clean imports)
  CQ-04: 1/2   (ok but slightly verbose)
  CQ-05: 1/1   (correct output)

LIBRARY MASTERY (9/10)
  LM-01: 5/5   (idiomatic usage)
  LM-02: 4/5   (uses some distinctive features)

TOTAL: 76/100 = "Good" Tier → Repair loop
```

Note: This plot scored well on technical criteria but only 8/20 on Design Excellence. To reach 90+, it needs better aesthetic sophistication (DE-01), visual refinement (DE-02), and data storytelling through visual emphasis and hierarchy (DE-03).
