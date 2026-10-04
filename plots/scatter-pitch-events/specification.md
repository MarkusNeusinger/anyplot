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
- `end_x`, `end_y` (numeric, optional) — end position in meters for passes and shots; empty for tackles and interceptions
- Size: 50–500 events per match segment
- Example: synthetic match event data with coordinates, event types, and outcomes distributed across pitch zones

## Notes

- Draw an accurate pitch outline with standard FIFA dimensions (105m × 68m) including penalty areas, goal areas, center circle, halfway line, corner arcs, and goal posts
- Use distinct marker shapes and colors for each event type (e.g., circles for passes, stars for shots, triangles for tackles, diamonds for interceptions)
- Encode outcome (successful/unsuccessful) via marker fill or opacity (e.g., filled vs hollow, or high vs low opacity)
- Show directional arrows for passes and shots indicating start-to-end or trajectory direction
- Use a green or white pitch background with contrasting line colors for clear readability
- Maintain correct aspect ratio matching the 105:68 pitch proportions

## What a good version looks like

- A good version shows: the pitch outline in the standard FIFA dimensions with penalty areas, goal areas, center circle, halfway line, corner arcs and goal posts, as the Notes ask, every marking in its true position and proportion and the corner arcs curving into the pitch.
- A good version shows: the 105:68 aspect ratio, as the Notes ask, so the center circle is round and the whole pitch is in view, on a green or white pitch background with line colors that contrast with it in both themes.
- A good version shows: a distinct marker shape and color for each event type, as the Notes ask, every marker sitting at its event's pitch coordinates and never moved to thin out a crowded area.
- A good version shows: the outcome encoded through marker fill or opacity, as the Notes ask, so successful and unsuccessful events of one type can be told apart while the unsuccessful ones remain visible on the pitch background.
- A good version shows: directional arrows for passes and shots, as the Notes ask, each anchored at its event's position, pointing to its end position where the data gives one, with a visible arrowhead that gives the direction, and fine enough that the markers stay readable beneath them.
- Expected, not a defect: markers and arrows crowding in front of goal and in midfield, shot arrows fanning into one goal mouth, arrows crossing each other, empty stretches of the pitch, and axis ticks and labels left out, since the pitch markings give the spatial reference.
