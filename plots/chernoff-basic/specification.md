# chernoff-basic: Chernoff Faces for Multivariate Data

## Description

Chernoff faces visualize multivariate data by mapping each variable to a facial feature (eye size, mouth curvature, face width, nose length, etc.), transforming each observation into a unique cartoon face. This technique leverages humans' innate ability to recognize and distinguish faces, making it easier to identify patterns, clusters, and outliers across multiple dimensions simultaneously.

## Applications

- Comparing financial health indicators across companies where each face represents a company's performance metrics
- Visualizing patient health profiles in medical research where facial features encode vital signs and lab results
- Analyzing customer segments in marketing where each face represents a customer profile with demographic and behavioral attributes

## Data

- `observation_id` (categorical) - Unique identifier for each observation/face
- `variable_1` through `variable_n` (numeric) - Continuous variables mapped to facial features (typically 5-15 variables)
- Size: 5-50 observations (faces become hard to compare with too many)
- Example: Iris dataset with 4 measurements per flower, or car ratings with multiple performance metrics

## Notes

- Each variable should be normalized to a common scale (0-1) before mapping to facial features
- Common feature mappings: face width, face height, eye size, eye spacing, eyebrow slant, nose length, mouth curvature, mouth width
- Grid layout recommended for comparing multiple faces side by side
- Consider colorizing faces by group membership if categorical grouping exists
- Include a key that names which variable drives each facial feature (a legend, caption or labeled example face)

## What a good version looks like

- A good version shows: one cartoon face per observation, all built from the same set of facial features, each variable driving the size, shape or position of one feature, so that faces differ visibly from one observation to the next.
- A good version shows: the faces side by side in a grid, as the Notes recommend, each identified by its observation label; position in the grid is layout, not data, and the figure has no data axes.
- A good version shows: features that stay recognizable as parts of a face at both ends of their range, the result of normalizing every variable to a common scale before mapping it, as the Notes ask.
- A good version shows: a key that tells which variable drives which facial feature, as the Notes ask, so the faces can be decoded.
- A good version shows: the basic variant's faces and their key, with the color by group the Notes allow and its legend, and no reference lines, highlighted faces or bands, callouts, asymmetric faces, or other charts beside the grid.
- Expected, not a defect: faces of different width and height, odd or exaggerated expressions, faces that look alike for similar observations, features whose changes are subtle, and an order of faces that carries no value.
