# scatter-pitch-events: Soccer Pitch Event Map

## Description

A soccer pitch event map positions match events (passes, shots, tackles, interceptions) as markers on an accurately scaled football pitch diagram. The pitch is drawn with standard markings including penalty areas, center circle, goal areas, and halfway line. Each event type uses distinct markers and colors, with directional arrows for passes and shots. This visualization is essential for tactical match analysis, scouting, and coaching in football analytics.

## Applications

- Analyzing pass networks and attacking build-up patterns during a match
- Scouting player positioning, defensive actions, and pressing zones
- Visualizing shot locations with outcome encoding for expected goals (xG) analysis
- Post-match tactical review comparing event distributions across pitch zones

## Data

- `x` (numeric) — horizontal pitch position in meters (0–105)
- `y` (numeric) — vertical pitch position in meters (0–68)
- `event_type` (categorical) — type of event: pass, shot, tackle, interception
- `outcome` (categorical) — result of the event: successful, unsuccessful
- Size: 50–500 events per match segment
- Example: synthetic match event data with coordinates, event types, and outcomes distributed across pitch zones

## Notes

- Draw an accurate pitch outline with standard FIFA dimensions (105m × 68m) including penalty areas, goal areas, center circle, halfway line, corner arcs, and goal posts
- Use distinct marker shapes and colors for each event type (e.g., circles for passes, stars for shots, triangles for tackles, diamonds for interceptions)
- Encode outcome (successful/unsuccessful) via marker fill or opacity (e.g., filled vs hollow, or high vs low opacity)
- Show directional arrows for passes and shots indicating start-to-end or trajectory direction
- Use a green or white pitch background with contrasting line colors for clear readability
- Maintain correct aspect ratio matching the 105:68 pitch proportions
