# {specification-id}: {Title}

## Description

{2-4 sentences describing what this plot visualizes and when to use it. What makes it useful? What insights does it reveal?}

## Applications

- {Realistic scenario with domain context}
- {Another use case}
- {Third use case}

## Data

- `{column_name}` ({type}) - {what this column represents}
- `{column_name}` ({type}) - {what this column represents}
- Size: {recommended data size, e.g., 50-500 points}
- Example: {dataset reference or inline data description}

## Notes

- {Optional implementation hints, special requirements, or visual preferences}
- {Optional, for domain diagrams whose values can be right or wrong — `Check values:` one to three numbers a correct implementation reproduces from its own computation, never hard-coded, each with its configuration and source}

## What a good version looks like

- A good version shows: {an observable property of a good render of THIS plot type — something a viewer sees in the image, not a code instruction}
- Expected, not a defect: {something that can look like a flaw but is inherent to the plot type, with no instruction attached — e.g. "overlapping bubbles in dense regions"}
- A good version shows: {how a good version handles the expected item, phrased conditionally so it never turns the permission into a target — e.g. "where bubbles overlap, translucency and a thin outline keep each one distinguishable, and every bubble stays at its (x, y) values"}
- A good version shows: {the variant's scope — for a `-basic` spec, "the basic variant's …" with exactly the encodings the Data section lists. Derived layers (trend or fit lines, mean or reference lines, bands, extra series, derived color scales, marginals, facets, callouts) are outside a basic variant; name reference lines, highlights and callouts in the bullet, as excluded or, where the Notes allow them, as allowed, because the review reads its list as complete; an id that names a field's standard diagram lists the layers its spec requires}
- A good version shows: {optional — more bullets of either kind, each with its own prefix; 3-6 in total, one kind per bullet, one line each, no numeric thresholds, no generic ideals such as "no overlap" or "clean design"}
