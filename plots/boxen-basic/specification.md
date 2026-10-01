# boxen-basic: Basic Boxen Plot (Letter-Value Plot)

## Description

A boxen plot (also known as letter-value plot) extends the traditional box plot to show more quantile information, making it ideal for large datasets with 1000+ observations. Instead of just displaying the median and quartiles, it shows additional "letter values" (eighths, sixteenths, etc.) as nested boxes, revealing the full shape of the distribution including tail behavior. This makes outlier detection more meaningful and distribution comparison more detailed.

## Applications

- Analyzing response time distributions across server clusters with millions of requests
- Comparing gene expression levels in large-scale genomics studies
- Quality control in manufacturing with high-volume production data
- Exploring salary or income distributions in large census datasets

## Data

- `category` (string) - group labels for comparison (optional for single distribution)
- `value` (numeric) - numerical values to plot
- Size: 1000-100000+ points per category, 1-8 categories
- Example: Server response times by endpoint, test scores by school

## Notes

- Show nested boxes representing letter values (median, quartiles, eighths, sixteenths, etc.)
- Boxes should decrease in width for deeper quantiles
- Use contrasting colors or shading to distinguish quantile levels
- Display outliers beyond the deepest letter value as individual points
- Include clear axis labels and legend explaining quantile levels

## What a good version looks like

- A good version shows: for each category a stack of nested boxes around a median mark, the innermost spanning the quartiles and each further box spanning the next letter value (eighths, sixteenths and so on) out into the tails, with every box edge at its quantile on the value axis.
- A good version shows: boxes that get narrower with each deeper quantile level, as the Notes ask, all centered on the category's position.
- A good version shows: contrasting colors or shading that tell the quantile levels apart in both themes, and a legend explaining which quantile level each one stands for, as the Notes ask.
- A good version shows: observations beyond the deepest letter value as individual points at their values, as the Notes ask.
- A good version shows: the basic variant's nested letter-value boxes, and, besides them, the median mark, the outlier points and the quantile-level legend, no whiskers, overlaid strip or swarm points, density shapes, mean markers, reference or mean lines, highlighted boxes or bands, or callouts.
- Expected, not a defect: many nested boxes for a large sample, a different number of levels in categories of different size, thin slivers for the deepest levels, tails of unequal length on the two sides of the median, and many outlier points in a very large sample.
