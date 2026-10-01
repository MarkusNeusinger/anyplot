# chord-basic: Basic Chord Diagram

## Description

A chord diagram displays relationships or flows between entities arranged around a circle's perimeter. Arcs (chords) connect related entities, with chord width proportional to the flow magnitude. This visualization excels at revealing the overall structure of connections and identifying the strongest relationships within a system.

## Applications

- Visualizing migration flows between countries or regions
- Showing trade relationships and import/export volumes between nations
- Displaying gene interactions or protein-protein interactions in bioinformatics
- Analyzing communication patterns between departments in an organization

## Data

- `source` (categorical) - Origin entity/group name
- `target` (categorical) - Destination entity/group name
- `value` (numeric) - Flow magnitude or connection strength
- Size: 4-20 entities with 10-100 connections
- Example: Migration flows between 6 continents with bidirectional flow values

## Notes

- Each entity should have a distinct color for easy identification
- Chord width should be proportional to flow value
- Consider adding hover tooltips showing exact flow values for interactive libraries
- For bidirectional flows, both directions should be visible as separate chords

## What a good version looks like

- A good version shows: every entity as an arc on the perimeter of one circle, labeled at its arc, with an arc length that grows with the entity's total flow; the order of entities around the circle is a layout choice, not data.
- A good version shows: chords through the interior joining the arcs of related entities, each with a width proportional to its flow value, as the Notes ask, and anchored on the arcs of the two entities it connects.
- A good version shows: one distinct color per entity, as the Notes ask, with each chord taking the color of an entity it connects and translucent enough that chords crossing it stay distinguishable in both themes.
- A good version shows: for a pair with flows in both directions, the two directions visible as separate chords, as the Notes ask.
- A good version shows: the basic variant's ring of entity arcs, their labels and the chords, with the hover tooltips the Notes suggest in interactive output: no extra data tracks or rings, highlighted chords or arcs, reference lines, callouts or annotations of the strongest flow.
- Expected, not a defect: chords that cross and pile up in the middle of the circle, blended color where they overlap, hair-thin chords for small flows, and arcs of very unequal length.
