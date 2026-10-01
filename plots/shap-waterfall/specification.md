# shap-waterfall: SHAP Waterfall Plot for Feature Attribution

## Description

A waterfall-style chart showing how each feature contributes to pushing a model prediction from a base value (expected model output) to the final predicted value. Horizontal bar segments extend right for positive SHAP values and left for negative SHAP values, stacking cumulatively so the viewer can trace the path from baseline to prediction. This is a core ML explainability visualization for explaining individual predictions, complementing the SHAP summary plot which shows feature effects across many samples.

## Applications

- Explaining individual predictions in credit scoring models to auditors or loan applicants
- Debugging unexpected model outputs in healthcare ML by identifying which features drove the prediction
- Communicating feature impact to non-technical stakeholders in business decision-making
- Satisfying regulatory compliance requirements for model explainability (e.g., GDPR right to explanation)

## Data

- `feature` (str) - Feature names (e.g., "Age", "Income", "Credit Score")
- `shap_value` (float) - SHAP contribution value per feature (positive pushes prediction up, negative pushes down)
- `base_value` (float) - Expected model output (mean prediction across training data), single scalar
- `final_value` (float) - Actual model prediction for this instance (base_value + sum of SHAP values), single scalar
- Size: 10-20 features typical; show top features by absolute SHAP magnitude

## Notes

- Order features by absolute SHAP value magnitude (largest contribution at top)
- Cumulative bar segments flow from base_value to final_value
- Color bars red/pink for positive SHAP contributions and blue for negative contributions
- Display base value and final prediction value as labeled reference lines or annotations
- Show numeric SHAP values on or beside each bar segment
- Use a horizontal layout with feature names on the y-axis for readability
- Consider a connector line between segments to emphasize the cumulative flow

## What a good version looks like

- A good version shows: one horizontal bar segment per displayed feature, with at most one more for the remaining features taken together, each starting where its neighbor ends, extending right for a positive contribution and left for a negative one, so the chain runs unbroken from the base value to the final prediction, as the Notes ask.
- A good version shows: the features ordered by the absolute size of their contribution with the largest at the top, as the Notes ask, and the feature names on the y axis.
- A good version shows: positive contributions in red or pink and negative ones in blue, as the Notes ask, the two told apart in both themes.
- A good version shows: the base value and the final prediction as labeled reference lines or annotations, as the Notes ask, each at the end of the chain it belongs to.
- A good version shows: the numeric contribution on or beside each bar segment, as the Notes ask, readable for the shortest segments too.
- Expected, not a defect: segments of very unequal length down to slivers, a value axis that covers only the range of the chain and leaves out zero, a chain that doubles back where signs alternate, and one collapsed row for the remaining features.
