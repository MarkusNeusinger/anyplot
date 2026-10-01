# scatter-shot-chart: Basketball Shot Chart

## Description

A basketball shot chart overlays shooting data on a half-court diagram, plotting each shot attempt as a point colored by outcome (made or missed). The court drawing includes the three-point arc, free-throw line, paint/key area, and basket, providing spatial context for analyzing shooting patterns and efficiency. Essential for basketball analytics and player evaluation.

## Applications

- Analyzing a player's shooting tendencies and field-goal percentage by court zone
- Scouting opposing players to identify their preferred and weakest shooting locations
- Evaluating team offensive strategies and shot selection patterns
- Sports journalism and broadcast graphics summarizing game or season performance

## Data

- `x` (numeric) — horizontal court position in feet from the basket center
- `y` (numeric) — vertical court position in feet from the basket center
- `made` (boolean) — shot outcome (True = made, False = missed)
- `shot_type` (categorical) — type of shot: "2-pointer", "3-pointer", "free-throw"
- Size: 200-500 shot attempts per player

## Notes

- Draw an accurate NBA half-court outline using standard dimensions (50 ft wide x 47 ft deep): three-point arc (23.75 ft at top, 22 ft in corners), free-throw line (15 ft from backboard), paint/key area (16 ft wide), restricted area arc, and basket/backboard
- Plot each shot as a point: green for made, red for missed
- Court lines should be drawn in a neutral color (gray or black) so shot markers stand out
- The court should fill the plot area with minimal padding; axis ticks and labels are optional since the court geometry provides spatial reference
- Use a 1:1 aspect ratio so the court is not distorted
- Optionally include a legend for made/missed and shot type

## What a good version looks like

- A good version shows: an NBA half-court outline in the standard dimensions the Notes give, with the three-point arc, closer to the basket in the corners than at the top, the free-throw line, the paint, the restricted area arc and the basket with its backboard, each in its true place and proportion.
- A good version shows: a 1:1 aspect ratio, as the Notes ask, so the hoop and the arcs are circular and not stretched, with the court filling the plot area with minimal padding.
- A good version shows: every shot attempt as a point at its court coordinates relative to the basket, never jittered, binned or moved to thin out a crowded area.
- A good version shows: made shots in green and missed shots in red, as the Notes ask, over court lines in a neutral gray or black, so the shot markers stand out from the court and the two outcomes can be told apart in both themes.
- A good version shows: a legend for made and missed shots and for shot type, if drawn, as the Notes allow, matching the markers on the court; shot type, if encoded by marker shape or size, is explained there.
- Expected, not a defect: shots piling up and overlapping near the basket, thinner coverage in the mid-range, empty floor toward the half-court line, free throws stacked on one spot, and axis ticks and labels left out, since the court geometry gives the spatial reference.
