# Spec Tags Generator

AI rules for assigning Specification-Level Tags.

---

## Naming Convention

**For ALL tags:**
- All lowercase
- Hyphens for multi-word: `color-mapped`, `time-series`, `flow-visualization`
- No underscores, no spaces
- Prefer established terms from the data visualization community

---

## The 4 Tag Dimensions

### Vocabulary policy

The lists below are **canonical for `plot_type`** (any new plot type should be added here via PR before being used), and **advisory for `data_type` / `domain` / `features`** (they list common values; any well-formed, recognized data-viz term is allowed in those three dimensions).

The polish workflow enforces this asymmetry:
- It will **move** tags from one dimension to another when they're clearly misclassified (e.g. `timeseries` in `plot_type` → `data_type`, `regression` in `plot_type` → `features`).
- It will **only remove** an out-of-vocab tag from `plot_type` (where the list is canonical). For `data_type` / `domain` / `features`, an unfamiliar but well-formed tag is left in place.
- It will always **canonicalize** naming (lowercase, hyphens, no underscores) and prefer the canonical term when one exists (`multi-series` → `multi`, `sequential` → `stepwise`).

### 1. plot_type - "What is visualized?"

**Purpose:** Describes the visual form and structure of the plot.

**Question:** "How would a data visualization expert name this plot?"

**Vocabulary (canonical — additions to this table are gated on a PR):**

| Category | Tags |
|----------|------|
| Basic Forms | `scatter`, `line`, `bar`, `pie`, `area`, `point`, `bubble` |
| Distributions | `histogram`, `density`, `box`, `violin`, `strip`, `swarm`, `rug` |
| Matrices | `heatmap`, `contour`, `hexbin` |
| Hierarchies | `treemap`, `sunburst`, `dendrogram`, `icicle`, `circlepacking` |
| Networks | `network`, `chord`, `arc`, `sankey`, `alluvial` |
| Specialized | `candlestick`, `gauge`, `funnel`, `waterfall`, `radar`, `polar`, `gantt`, `mosaic`, `donut`, `barcode`, `pairplot`, `surface`, `step` |
| Geospatial | `choropleth`, `map` |
| Statistical | `qq`, `ecdf`, `calibration`, `bland-altman` |

**Rules:**
- Use established names from matplotlib/seaborn/plotly documentation
- Multiple tags allowed when plot combines multiple types — but every value must come from this canonical table
- `flow`, `temporal`, `multi`, etc. are NOT plot types. They go in `features` (where they describe a property of the visualization). A Sankey diagram is `plot_type: sankey` plus `features: flow`.
- If a spec needs a plot type not on this list, add the tag to this table first (in the same PR or earlier) — that's the only place where vocabulary expansion is intentionally gated

---

### 2. data_type - "What data is visualized?"

**Purpose:** Describes the structure and nature of the input data.

**Question:** "If someone has this type of data, would they search for this plot?"

**Common values (advisory — any well-formed, recognized data-shape term is allowed):**

| Category | Tags |
|----------|------|
| Numbers | `numeric`, `continuous`, `discrete`, `binary`, `probability` |
| Variates | `univariate`, `bivariate`, `multivariate` |
| Categories | `categorical`, `ordinal`, `compositional` |
| Time | `timeseries`, `datetime` |
| Structure | `hierarchical`, `network`, `relational`, `paired`, `directional` |
| Space | `geospatial`, `spatial`, `angular` |
| Text | `text`, `frequency` |
| Matrix | `matrix`, `correlation` |

Tags here describe what the **input data** looks like. Closely related visual properties (`temporal` axis, `flow` arrangement, etc.) belong in `features` instead.

**Rules:**
- Focus on logical data structure, not technical format
- Multiple tags when different data types are combined
- Example: Scatter needs `numeric` for both axes
- The table is a starting point — domain-specific shapes (`ohlc`, `genomic`, etc.) may be tagged when they're the spec's defining input

---

### 3. domain - "Where is it used?"

**Purpose:** Describes typical application areas.

**Question:** "Is there an industry where this plot is particularly common?"

**Common values (advisory — any real-world domain or sub-discipline is allowed):**

| Category | Tags |
|----------|------|
| Universal | `general` |
| Science | `statistics`, `science`, `research`, `physics`, `chemistry`, `biology`, `bioinformatics`, `genetics`, `geology` |
| Business | `business`, `finance`, `marketing`, `trading`, `logistics`, `project-management` |
| Technology | `engineering`, `technology`, `signal-processing`, `data-science` |
| Other | `healthcare`, `education`, `energy`, `environment`, `meteorology`, `transportation`, `politics`, `demographics` |
| ML/AI | `machine-learning`, `model-evaluation` |

**Rules:**
- `general` is default for universally applicable plots
- Specific domains only when plot is particularly established there
- Example: Candlestick → `finance`, Forest Plot → `healthcare`
- The table is illustrative — narrower disciplines (`econometrics`, `music`, `infrastructure`, `monitoring`, etc.) are valid when the spec is genuinely characteristic of that field

---

### 4. features - "What are special properties?"

**Purpose:** Describes variants, modifications, and special attributes.

**Question:** "What distinguishes this variant from the base version?"

**Common values (advisory — any meaningful feature descriptor is allowed):**

| Category | Tags |
|----------|------|
| Complexity | `basic`, `advanced` |
| Layout | `grouped`, `stacked`, `horizontal`, `multi`, `faceted`, `overlay`, `composite`, `combined` |
| Dimensions | `2d`, `3d` |
| Interaction | `interactive`, `animated`, `static` |
| Function | `comparison`, `distribution`, `correlation`, `ranking`, `regression`, `clustering`, `classification`, `model-evaluation`, `diagnostic` |
| Display | `annotated`, `color-mapped`, `proportional`, `normalized`, `printable` |
| Statistical | `confidence-interval`, `uncertainty`, `density`, `quartiles`, `threshold`, `trend` |
| Special | `flow`, `temporal`, `cumulative`, `stepwise`, `circular`, `radial`, `drilldown`, `technical-analysis` |

Canonical preferences (polish will rewrite legacy synonyms to these):
- `multi` (not `multi-series`) for "more than one series in the same chart"
- `flow` (not `flow-visualization`) for diagrams whose primary message is movement between states
- `stepwise` (not `sequential`) for staircase-style transitions
- `color-mapped` (not `labeled`) when the distinction is colour encoding

Tags describing data shape (`multivariate`, `hierarchical`, `directional`) belong in `data_type`, not here.

**Rules:**
- Describe what makes the plot SPECIAL
- Multiple tags allowed
- `basic` is informative — indicates base variant
- This table is a non-exhaustive starting point. New feature tags are encouraged when they capture a real distinction; prefer canonical wording (`stepwise` not `sequential`, `multi` not `multi-series` when describing layout, etc.)

---

## Output Format

```yaml
tags:
  plot_type:
    - {primary-type}
    - {secondary-type}  # optional
  data_type:
    - {primary-datatype}
    - {secondary-datatype}  # optional
  domain:
    - general  # always when universally applicable
    - {specific-domain}  # optional
  features:
    - basic  # or specific features
    - {additional-features}
```

---

## Examples

### scatter-basic
```yaml
tags:
  plot_type:
    - scatter
  data_type:
    - numeric
    - continuous
  domain:
    - statistics
    - general
  features:
    - basic
    - 2d
    - correlation
```

### sankey-basic
```yaml
tags:
  plot_type:
    - sankey
    - flow
  data_type:
    - categorical
    - numeric
  domain:
    - general
    - business
  features:
    - basic
    - flow
    - proportional
```

### heatmap-calendar
```yaml
tags:
  plot_type:
    - heatmap
    - calendar
  data_type:
    - datetime
    - numeric
  domain:
    - general
    - business
  features:
    - basic
    - temporal
    - color-mapped
```

---

## Best Practices

1. **Specific but not excessive** - 2-4 tags per dimension is typical
2. **Think like a user** - What would someone type in a search?
3. **Use established terms** - Prefer listed vocabulary, but any recognized term from the data-viz community is valid in `data_type`, `domain`, and `features`. `plot_type` is the only dimension where the table is canonical.
4. **general is OK** - Not every plot needs a specialized domain
5. **basic is informative** - Indicates this is the base variant
6. **Right-dimension matters more than perfect-vocabulary** - A statistical operation like `regression` belongs in `features`, not `plot_type`. A data-shape like `timeseries` belongs in `data_type`, not `plot_type`. The polish workflow will move misclassified tags to the right dimension rather than just dropping them.
