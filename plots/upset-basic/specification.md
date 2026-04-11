# upset-basic: UpSet Plot for Multi-Set Intersection Analysis

## Description

An UpSet plot visualizes intersections of multiple sets using a matrix-based layout that scales far better than Venn diagrams beyond 3 sets. A horizontal bar chart shows individual set sizes, a dot-matrix indicates which sets participate in each intersection, and a vertical bar chart above shows the intersection cardinality. This is the modern standard for set intersection analysis, making complex overlaps between many sets immediately readable.

## Applications

- Comparing gene sets from multiple genomic experiments to identify shared and unique biological pathways
- Analyzing feature overlap across machine learning model versions to understand model evolution
- Visualizing user segments across multiple marketing criteria to find high-value audience intersections
- Showing bug categories that overlap across software modules to prioritize cross-cutting issues

## Data

- `element` (str) — unique item identifier
- `sets` (list[str]) — which sets this element belongs to (each element can belong to one or more sets)
- Size: 4–15 sets, 100–10,000 elements
- Example: genomic experiment results where each gene (element) belongs to one or more differential expression sets

## Notes

- Intersections should be sorted by size (descending) by default, with degree-based sorting as an alternative
- Connected dots in the matrix show which sets form each intersection; unconnected dots indicate non-membership
- Horizontal bars on the left show individual set sizes (total members per set)
- Vertical bars on top show intersection cardinality (number of elements in each specific intersection)
- Matrix rows represent sets; columns represent unique intersections
- Lines connecting dots in the same column should be clearly visible to indicate set combinations
- Consider using color or shading to distinguish intersection degree (number of sets involved)
- Superior to Venn diagrams for more than 3 sets; complements the existing venn-basic specification
