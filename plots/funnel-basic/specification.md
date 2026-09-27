# funnel-basic: Basic Funnel Chart

## Description

A funnel chart visualizes sequential stages of a process where values progressively decrease from one stage to the next. Each stage is represented as a trapezoidal segment that narrows from top to bottom, making it easy to identify drop-offs between stages. This chart is ideal for tracking conversion rates, sales pipelines, and multi-step processes where understanding stage-to-stage transitions is critical.

## Applications

- Marketing teams tracking website visitor conversion from awareness through purchase
- Sales organizations visualizing pipeline stages from leads to closed deals
- HR departments analyzing recruitment funnel from applications to hires
- E-commerce platforms monitoring checkout abandonment at each step

## Data

- `stage` (string) - Name of each sequential stage in the process
- `value` (numeric) - Count or amount at each stage, typically decreasing
- Size: 3-8 stages (too many stages reduce readability)
- Example: Sales funnel with stages ["Awareness", "Interest", "Consideration", "Intent", "Purchase"] and values [1000, 600, 400, 200, 100]

## Notes

- Stages should be ordered from largest (top) to smallest (bottom)
- Use distinct colors for each stage to improve visual differentiation
- Include value or percentage labels on each segment for clarity
- The width of each segment should be proportional to its value relative to the first stage

## What a good version looks like

- A good version shows: one segment per stage, stacked in process order from the largest at the top to the smallest at the bottom, each centered on one vertical axis with its width proportional to its value relative to the first stage.
- A good version shows: one distinct color per stage, as the Notes ask, and each stage's name beside or on its segment.
- A good version shows: every segment labeled with its value or its percentage, readable against its own fill in both themes.
- A good version shows: the basic variant's single funnel: one segment per stage and no second funnel, comparison series or drop-off callouts between the stages.
- Expected, not a defect: widths that shrink at every step, drops of very different size between stages, and centered trapezoids or slanted connectors between segments; the narrowing is how a funnel is built.
