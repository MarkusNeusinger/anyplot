# scatter-text: Scatter Plot with Text Labels Instead of Points

## Description

A scatter plot where data points are represented by text labels instead of markers. Each label is positioned at its corresponding coordinates, making the text itself the visual element. This visualization is particularly useful for displaying named entities in 2D space, such as word embeddings, dimensionality reduction outputs, or any scenario where identifying individual items by name is more important than seeing their relative density.

## Applications

- Visualizing word embeddings or document embeddings after t-SNE or UMAP dimensionality reduction
- Displaying product or brand positioning in a competitive landscape analysis
- Showing author or journal relationships in bibliometric studies
- Mapping company positions based on two business metrics where company names matter

## Data

- `x` (numeric) - Horizontal coordinate for each text label
- `y` (numeric) - Vertical coordinate for each text label
- `label` (string) - The text to display at each coordinate position
- Size: 20-100 points recommended to balance readability and visual density
- Example: Named entities with 2D coordinates from dimensionality reduction

## Notes

- Text labels should be legible with appropriate font size
- Consider using alpha transparency when labels overlap
- Font size may need adjustment based on the number of labels
- For dense regions, consider rotating text or using smaller fonts
- Color can encode additional categorical or numeric information

## What a good version looks like

- A good version shows: each item drawn as its text label in place of a marker, every label anchored the same way, typically centered, on its exact (x, y) value, so the word itself marks the position.
- A good version shows: text large enough that every isolated label can be read in both themes, in a font size that fits the number of labels, as the Notes ask.
- A good version shows: in dense regions, translucency, smaller text or rotation, as the Notes suggest, so overlapping labels can still be made out; labels are not moved away from their coordinates to separate them.
- A good version shows: color, if used as the Notes allow, explained by a legend for categories or a color bar for a numeric variable, with every color legible as text against the page in both themes.
- Expected, not a defect: labels that partly overlap where items sit close together, labels of different length covering different areas, and empty regions between clusters.
