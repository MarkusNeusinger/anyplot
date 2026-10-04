# circos-basic: Circos Plot

## Description

A Circos plot is a circular visualization that displays data on concentric tracks arranged around a circle, with ribbons or arcs connecting related segments across the circular layout. Originally designed for genomic data visualization, it excels at showing relationships between segments while simultaneously displaying multiple data attributes on different tracks. The circular arrangement makes efficient use of space and reveals patterns in complex relational data.

## Applications

- Visualizing chromosomal rearrangements and genomic structural variations in bioinformatics
- Displaying trade flows or migration patterns between countries or regions
- Showing dependencies and relationships between software modules or system components
- Analyzing co-occurrence or correlation patterns between categorical variables

## Data

- `source` (categorical) - Origin segment or category identifier
- `target` (categorical) - Destination segment or category identifier
- `value` (numeric) - Connection strength or flow magnitude between segments
- `segment_size` (numeric, optional) - Size of each segment on the outer ring
- `track_data` (numeric) - Values for 1-3 concentric data tracks (at least one)
- Size: 5-30 segments with 10-100 connections
- Example: Genomic data showing 10 chromosomes with inter-chromosomal connections and expression values on inner tracks

## Notes

- Segments should be arranged around the circle with gaps for visual separation
- Ribbon width should be proportional to the connection value
- Use distinct colors for each segment to aid identification
- Draw 1-3 concentric tracks inside the outer ring for additional data layers
- For genomic applications, segments typically represent chromosomes with consistent color coding

## What a good version looks like

- A good version shows: an outer ring of labeled segments around one circle, separated by gaps, as the Notes ask, with arc lengths that follow the segment sizes when the data gives them; the order of segments is a natural one, such as chromosome order, or a layout choice.
- A good version shows: ribbons across the interior connecting related segments, each with a width proportional to its connection value, as the Notes ask, and anchored on the two segments it connects.
- A good version shows: one distinct color per segment, as the Notes ask, used consistently for the segment and whatever is colored by it, with ribbons translucent enough that those crossing them stay distinguishable in both themes.
- A good version shows: one to three concentric data tracks, as the Notes ask, drawn as rings inside the outer ring, aligned with the angular span of the segments they describe, visually separate from the ribbons, and explained by a legend or caption.
- A good version shows: the basic variant's segment ring, ribbons and the inner data tracks the Notes ask for: no highlighted ribbons or segments, reference lines, callouts or annotations of the strongest connection, or second circle or panel.
- Expected, not a defect: ribbons that cross and pile up in the middle of the circle, blended color where they overlap, hair-thin ribbons for weak connections, and segments of very unequal length.
