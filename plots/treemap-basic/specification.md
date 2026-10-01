# treemap-basic: Basic Treemap

## Description

A treemap displaying hierarchical data as nested rectangles, where each rectangle's area is proportional to its value. This visualization excels at showing part-to-whole relationships in hierarchical structures, making it easy to spot large and small items at a glance. Treemaps efficiently use screen space to display large amounts of hierarchical data in a compact form.

## Applications

- Disk space usage visualization by folder and file size
- Budget allocation breakdown by department and project
- Market capitalization comparison by sector and company
- Website traffic analysis by country and city

## Data

- `category` (string) - main category or parent group
- `subcategory` (string) - optional sub-category for nested hierarchy
- `value` (numeric) - size/magnitude determining each rectangle's area
- Size: 5-50 items
- Example: Company expense breakdown by department and cost center, or product catalog by category and subcategory with sales volume

## Notes

- Use distinct colors for main categories to aid quick identification
- Add labels for larger rectangles; smaller ones may omit labels for clarity
- Include subtle borders between rectangles to show hierarchy boundaries
- Show hierarchy through nesting depth or color shading intensity

## What a good version looks like

- A good version shows: rectangles that tile the plot area, each with an area proportional to its value, laid out as compact blocks rather than long thin slivers wherever the values allow.
- A good version shows: when the data has subcategories, each main category's rectangles sitting together as one block, with the two levels told apart through nesting depth or color shading intensity, as the Notes ask.
- A good version shows: a distinct color per main category and subtle borders between rectangles that mark the hierarchy boundaries, as the Notes ask, both visible in both themes.
- A good version shows: labels on the larger rectangles, as the Notes ask, each inside its own rectangle and readable against its fill in both themes.
- A good version shows: the basic variant's rectangles, besides the labels and borders the Notes ask for: position comes from the layout, not from data, so no axes or grid, and no color scale for a second variable, reference lines, highlighted rectangles or callouts.
- Expected, not a defect: rectangles of very different size and shape, including a dominant one, a few elongated ones and small unlabeled ones; unequal areas are the point of the chart.
