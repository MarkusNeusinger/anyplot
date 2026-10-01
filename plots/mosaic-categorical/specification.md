# mosaic-categorical: Mosaic Plot for Categorical Association Analysis

## Description

A mosaic plot visualizes contingency tables by dividing a rectangular area into smaller rectangles whose areas are proportional to cell frequencies. This statistical visualization technique effectively shows relationships and associations between two or more categorical variables, making it easy to identify patterns, dependencies, and deviations from expected frequencies in cross-tabulated data.

## Applications

- Analyzing survey response patterns across demographic groups
- Exploring relationships between categorical variables in social science research
- Visualizing contingency tables in medical studies (treatment vs outcome)
- Examining association between product categories and customer segments

## Data

- `category_1` (categorical) - First categorical variable (rows in contingency table)
- `category_2` (categorical) - Second categorical variable (columns in contingency table)
- `frequency` (numeric, optional) - Count or frequency for each combination; if omitted, computed from data
- Size: Typically 2-6 levels per categorical variable for readability
- Example: Titanic survival data cross-tabulated by class and survival status

## Notes

- Rectangle widths represent marginal proportions of the first variable
- Rectangle heights within each column represent conditional proportions of the second variable
- Area of each rectangle is proportional to the cell frequency in the contingency table
- Use statsmodels.graphics.mosaicplot for the core visualization
- Color coding can indicate residuals or deviations from independence
- Gap spacing between rectangles helps distinguish categories
- Labels should identify both categorical variables clearly

## What a good version looks like

- A good version shows: one rectangle per cell of the contingency table, the column widths following the marginal proportions of the first variable and the heights within each column the conditional proportions of the second, so each rectangle's area is proportional to its cell frequency.
- A good version shows: each category's block readable as a unit, set apart by the small gaps the Notes suggest or by clear borders, with the proportions of the tiles preserved.
- A good version shows: labels that identify both variables and their levels, as the Notes ask: the first variable's levels along the columns and the second variable's levels along the other edge or in a legend.
- A good version shows: color that encodes one stated thing: the levels of one of the two variables, applied the same way in every column, or the residuals from independence the Notes allow, with a legend, a key or the edge labels making plain which.
- Expected, not a defect: columns of very different width, small or sliver tiles for rare cells that are left unlabeled, and tile boundaries that sit at a different height in every column, which is how the plot shows association.
