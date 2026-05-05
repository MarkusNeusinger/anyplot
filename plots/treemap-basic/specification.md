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
