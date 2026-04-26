# Tagging System

anyplot uses a two-level tagging system:
- **Spec-Level Tags** (4 dimensions) - describe WHAT is visualized
- **Impl-Level Tags** (5 dimensions) - describe HOW it is implemented

---

## Naming Convention

**For ALL tags (both levels):**
- All lowercase
- Hyphens for multi-word: `color-mapped`, `twin-axes`, `time-series`
- No underscores, no spaces
- Prefer established terms

---

## Part 1: Spec-Level Tags

Spec-Level Tags are assigned during specification creation and apply to ALL library implementations of a plot.

Stored in: `plots/{spec-id}/specification.yaml`

### The 4 Spec Tag Dimensions

#### 1. plot_type - "What is visualized?"

Describes the visual form and structure of the plot.

**Typical Values:**
- **Basic Forms:** `scatter`, `line`, `bar`, `pie`, `area`, `point`
- **Distributions:** `histogram`, `density`, `box`, `violin`, `strip`, `swarm`
- **Matrices:** `heatmap`, `contour`, `hexbin`
- **Hierarchies:** `treemap`, `sunburst`, `dendrogram`, `icicle`
- **Networks:** `network`, `chord`, `arc`, `sankey`, `alluvial`
- **Specialized:** `candlestick`, `gauge`, `funnel`, `waterfall`, `radar`

#### 2. data_type - "What data is visualized?"

Describes the structure and nature of the input data.

**Typical Values:**
- **Numbers:** `numeric`, `continuous`, `discrete`
- **Categories:** `categorical`, `ordinal`
- **Time:** `timeseries`, `datetime`
- **Structure:** `hierarchical`, `network`, `relational`
- **Space:** `geospatial`, `spatial`

#### 3. domain - "Where is it used?"

Describes typical application areas.

**Typical Values:**
- **Universal:** `general`
- **Science:** `statistics`, `science`, `research`
- **Business:** `business`, `finance`, `marketing`
- **Technology:** `engineering`, `technology`
- **Other:** `healthcare`, `education`, `machine-learning`

#### 4. features - "What are special properties?"

Describes variants and special attributes.

**Typical Values:**
- **Complexity:** `basic`, `advanced`
- **Layout:** `grouped`, `stacked`, `horizontal`, `multi`
- **Dimensions:** `2d`, `3d`
- **Interaction:** `interactive`, `animated`
- **Function:** `comparison`, `distribution`, `correlation`

### Spec Tag Example

```yaml
# plots/scatter-basic/specification.yaml
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

---

## Part 2: Impl-Level Tags

Impl-Level Tags are assigned during implementation review and vary PER LIBRARY.

Stored in: `plots/{spec-id}/metadata/python/{library}.yaml`

### The 5 Impl Tag Dimensions

#### 1. dependencies - "Which external packages?"

External libraries beyond the main plotting library.

**Typical Values:**
`scipy`, `sklearn`, `statsmodels`, `networkx`, `selenium`, `pillow`, `geopandas`, `shapely`, `wordcloud`

**Rules:**
- Only tag when library is actually imported
- Do NOT tag numpy, pandas, and main plotting library

#### 2. techniques - "Which visualization techniques?"

Specific visualization and coding techniques.

**Typical Values:**
`twin-axes`, `manual-ticks`, `annotations`, `colorbar`, `subplots`, `faceting`, `layer-composition`, `custom-legend`, `inset-axes`, `polar-projection`, `3d-projection`, `bezier-curves`, `patches`, `hover-tooltips`, `html-export`

#### 3. patterns - "Which code structure patterns?"

Coding patterns and data organization.

**Typical Values:**
`data-generation`, `dataset-loading`, `wide-to-long`, `long-to-wide`, `groupby-aggregation`, `iteration-over-groups`, `matrix-construction`, `columndatasource`, `explicit-figure`

#### 4. dataprep - "Which data transformations?"

Statistical or mathematical transformations.

**Typical Values:**
`hierarchical-clustering`, `kde`, `binning`, `normalization`, `correlation-matrix`, `cumulative-sum`, `time-series`, `interpolation`, `rolling-window`, `pca`, `regression`

#### 5. styling - "Which visual style?"

Distinctive visual/aesthetic choices that deviate from defaults.

**Typical Values:**
`minimal-chrome`, `custom-colormap`, `alpha-blending`, `edge-highlighting`, `gradient-fill`, `grid-styling`, `dark-theme`

**Note:** `custom-colormap` is only for continuous color scales (cmap=), not manual color definitions.

### Impl Tag Example

```yaml
# plots/chord-basic/metadata/python/matplotlib.yaml
impl_tags:
  dependencies: []
  techniques:
    - bezier-curves
    - patches
    - manual-ticks
  patterns:
    - data-generation
    - matrix-construction
    - iteration-over-groups
  dataprep: []
  styling:
    - alpha-blending
```

---

## Comparison: Spec vs Impl Tags

| Aspect | Spec-Level Tags | Impl-Level Tags |
|--------|-----------------|-----------------|
| **Describes** | WHAT is visualized | HOW it is implemented |
| **Storage Location** | `specification.yaml` | `metadata/python/{library}.yaml` |
| **Applies to** | All 9 libraries | Only this library |
| **Assigned by** | `spec-create.yml` | `impl-review.yml` |
| **Dimensions** | 4 (plot_type, data_type, domain, features) | 5 (dependencies, techniques, patterns, dataprep, styling) |
| **Example** | "This is a scatter plot" | "This code uses twin-axes and scipy" |

---

## Use Cases

### Spec-Level Tags
- "Show all scatter plots" → `plot_type: scatter`
- "Plots for finance data" → `domain: finance`
- "3D visualizations" → `features: 3d`

### Impl-Level Tags
- "Which plots use scipy?" → `dependencies: scipy`
- "Implementations with twin-axes" → `techniques: twin-axes`
- "Code with clustering" → `dataprep: hierarchical-clustering`

---

## AI Prompts

For AI agents, there are separate, detailed prompt files:
- **Spec-Tags:** `prompts/spec-tags-generator.md`
- **Impl-Tags:** `prompts/impl-tags-generator.md`

These contain complete vocabulary, detection patterns, and examples.

---

## Best Practices

1. **Consistent naming convention** - lowercase, kebab-case
2. **Tag conservatively** - Only what is clearly recognizable
3. **Empty lists are OK** - Not every dimension needs to be filled
4. **2-4 tags per dimension** - Typical for spec tags
5. **3-8 tags total** - Typical for impl tags
6. **Use established terms** - Prefer listed vocabulary, but any recognized term from the data-viz/programming community is valid (e.g., unlisted libraries should still be tagged)
