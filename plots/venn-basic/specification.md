# venn-basic: Venn Diagram

## Description

A Venn diagram visualizes the logical relationships between two or three sets using overlapping circles. Each circle represents a set, and overlapping regions show elements shared between sets. This classic visualization is ideal for showing intersections, unions, and exclusive memberships, making abstract set relationships immediately intuitive.

## Applications

- Comparing feature overlap between product offerings or service tiers
- Analyzing survey responses where respondents may belong to multiple groups
- Visualizing gene expression overlap in biological research
- Illustrating shared and unique skills across team members or job candidates

## Data

- `set_labels` (list of strings) - Names for each set (2-3 sets)
- `set_sizes` (list of integers) - Total size of each set
- `intersections` (dict or list) - Sizes of pairwise and triple overlaps, inclusive (AB counts the ABC elements too)
- Size: 2-3 sets maximum for clarity
- Example: Three sets A, B, C with sizes 100, 80, 60 and overlaps AB=30, AC=20, BC=25, ABC=10

## Notes

- Limit to 2 or 3 circles for visual clarity (more circles become unreadable)
- Area proportional to size when possible (proportional Venn diagrams)
- Display the exclusive count (or percentage) of each region
- Use distinct colors with transparency to show overlapping areas clearly
- Ensure text labels are readable against all background colors

## What a good version looks like

- A good version shows: two or three overlapping circles, one per set, each named by its set label at or outside its circle, with every pairwise overlap and, for three sets, the triple overlap present as its own region.
- A good version shows: the exclusive count or percentage of each region, as the Notes ask, placed inside the region it belongs to and derived correctly from the inclusive set and intersection sizes in the data.
- A good version shows: circle and overlap areas that follow the set and intersection sizes as far as circles permit, as the Notes ask, so a larger set is never the smaller circle; where the circles sit is a layout choice, not data.
- A good version shows: one distinct translucent color per circle, as the Notes ask, so each overlap reads as a blend with its outlines visible, and region text readable against every fill in both themes.
- A good version shows: the basic variant's circles, set labels and region counts or percentages: no further set, highlighted or outlined focus region, reference lines, callouts, or item names listed inside the regions.
- Expected, not a defect: areas that match the sizes only approximately, because circles cannot always be exactly proportional, a small or empty region that still appears, and overlaps in blended hues close to each other.
