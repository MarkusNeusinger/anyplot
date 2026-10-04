# line-impurity-comparison: Gini Impurity vs Entropy Comparison

## Description

A theoretical comparison plot showing Gini impurity and entropy (information gain) as splitting criteria for decision trees across the probability range [0, 1]. Both curves are displayed on the same axes to illustrate their similar behavior and slight differences. This educational visualization helps understand the mathematical foundation of tree-based algorithms and why both criteria lead to similar tree structures in practice.

## Applications

- Machine learning education: explaining decision tree splitting criteria
- Algorithm comparison: understanding why Gini and entropy perform similarly
- Feature importance interpretation: theoretical foundation for tree-based models
- Textbook illustration: fundamental ML concept visualization

## Data

- `p` (numeric array) - probability values from 0 to 1 (100 points recommended)
- Gini impurity calculated as: 2 * p * (1 - p)
- Entropy calculated as: -p * log2(p) - (1-p) * log2(1-p), normalized to [0, 1]
- Size: 100 points for smooth curves

## Notes

- X-axis: probability p in range [0, 1]
- Y-axis: impurity value on a shared axis from 0 to 1
- Both curves should be clearly distinguishable with different colors/line styles
- Include legend explaining both metrics with their formulas
- Annotate maximum impurity point at p=0.5 (both maxima occur here)
- Handle edge cases at p=0 and p=1 where entropy is defined as 0
- Consider adding a light grid for readability

## What a good version looks like

- A good version shows: Gini impurity and entropy as two smooth arch-shaped curves on shared axes over the whole probability range, each symmetric about p = 0.5 and with the shape its formula in the Data gives: Gini peaking at 0.5 and entropy at 1.
- A good version shows: both curves drawn all the way to p = 0 and p = 1, where they reach zero, with no gap, spike or missing end where the entropy formula is undefined, as the Notes ask.
- A good version shows: the two curves clearly told apart by color or line style, as the Notes ask, also where they run close together near the ends of the range.
- A good version shows: a legend that explains both metrics with their formulas, as the Notes ask, the formulas set as readable mathematics and not as raw markup.
- A good version shows: the maximum impurity point at p = 0.5 annotated, as the Notes ask, with the marker or text placed at the peaks without covering them.
- Expected, not a defect: perfectly smooth curves without noise, because the plot is theoretical, and two curves of nearly the same shape.
