# scatter-categorical: Categorical Scatter Plot

## Description

A scatter plot where points are colored according to a categorical variable. Each category has a distinct color, allowing visual comparison of patterns across groups. A legend maps colors to category names.

## Applications

- Visualizing relationships between variables across different groups
- Comparing correlation patterns by category
- Identifying clusters in multivariate data
- Exploratory analysis with group membership

## Data

The visualization requires:
- **X variable**: First continuous/numeric variable
- **Y variable**: Second continuous/numeric variable
- **Category variable**: Categorical grouping variable

Example structure:
```
X     | Y     | Category
------|-------|----------
1.2   | 3.4   | Group A
2.1   | 4.5   | Group B
1.8   | 3.9   | Group A
...
```

## Notes

- Use distinct, colorblind-safe colors for categories
- Include legend for category identification
- Marker shapes can also vary by group for additional distinction
- Consider alpha transparency for overlapping points

## What a good version looks like

- A good version shows: one point per observation at its exact (x, y) value, colored by its category, with one color per category used consistently and a legend that names every category, as the Notes ask.
- A good version shows: category colors that are clearly distinct from each other and from the page in both themes, as the Notes ask; marker shapes, if varied by category as the Notes allow, follow the same grouping and appear in the same legend.
- A good version shows: where groups overlap, translucency or a thin marker outline, so points of one category remain visible among another, with no point jittered or moved off its values.
- Expected, not a defect: groups that overlap partly, groups of unequal size and spread, and stray points of one category inside another's cloud.
