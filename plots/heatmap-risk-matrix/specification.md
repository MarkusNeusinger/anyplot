# heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)

## Description

A 5x5 grid heatmap plotting risk likelihood against consequence severity, used to visualize and prioritize risks in project and enterprise risk management. Cells are color-coded from green (low risk) through yellow and orange to red (critical risk), with individual risk items plotted as labeled markers. The risk score for each cell is the product of likelihood and impact, and zones are labeled to indicate risk severity levels (Low, Medium, High, Critical).

## Applications

- Project management risk registers visualizing identified risks by probability and impact
- Enterprise risk management for strategic risk assessment and prioritization (ISO 31000)
- IT security threat assessment matrices mapping threat likelihood against business impact
- Safety engineering hazard analysis in construction, pharma, or military compliance

## Data

- `risk_name` (string) - short label identifying each risk item
- `likelihood` (integer, 1-5) - probability rating from rare (1) to almost certain (5)
- `impact` (integer, 1-5) - severity rating from negligible (1) to catastrophic (5)
- `category` (string, optional) - risk category for grouping (e.g., "Technical", "Financial", "Operational")
- Size: 5-20 individual risk items plotted on the matrix

## Notes

- Use a green-yellow-orange-red color gradient for the background grid cells based on the risk score (likelihood x impact)
- Axis labels should use descriptive terms: Likelihood axis (Rare, Unlikely, Possible, Likely, Almost Certain), Impact axis (Negligible, Minor, Moderate, Major, Catastrophic)
- Risk items should be plotted as labeled markers with slight jitter to avoid overlapping when multiple risks share the same cell
- Include zone labels or a legend indicating risk levels: Low (1-4), Medium (5-9), High (10-16), Critical (20-25)
- Grid lines should clearly delineate each cell of the matrix

## What a good version looks like

- A good version shows: the 5x5 grid of likelihood against impact with every cell delineated by grid lines, as the Notes ask, and both axes labeled with the descriptive terms the Notes list, in order from the lowest rating to the highest.
- A good version shows: cell backgrounds on a green-yellow-orange-red gradient that follows the risk score, the product of likelihood and impact, as the Notes ask, so the lowest-score corner is green and the opposite corner red.
- A good version shows: zone labels or a legend naming the risk levels (Low, Medium, High, Critical), as the Notes ask, agreeing with the cell colors.
- A good version shows: each risk item as a labeled marker inside the cell of its likelihood and impact, readable against the cell color in both themes; markers that share a cell are jittered slightly, as the Notes ask, and never leave that cell.
- A good version shows: marker color or shape, if it encodes the optional category, explained by legend entries of its own.
- Expected, not a defect: empty cells, several markers gathered in a single cell, markers off the cell center because of the jitter, and risk zones that run diagonally in uneven steps because the score is a product.
