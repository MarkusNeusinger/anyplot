# parliament-basic: Parliament Seat Chart

## Description

A semicircular parliament seat chart visualizes political party representation by arranging seats in concentric arcs. Each seat is displayed as an individual dot or segment, colored by party affiliation. This visualization is ideal for showing the composition of legislative bodies, election results, and voting bloc distributions at a glance.

## Applications

- Visualizing election results showing party seat distributions in parliament
- Displaying committee or board composition by faction or affiliation
- Analyzing voting bloc strength and coalition possibilities
- Comparing party representation across different legislative periods

## Data

- `party` (str) - Invented name of a fictional party or group
- `seats` (int) - Invented number of seats held by each party
- `color` (str) - Hex color code assigned to the party
- Size: 3-15 parties, total seats typically 50-700
- Example: A fictional chamber with made-up party names, made-up seat counts, and colors taken from the chart palette

## Notes

- Seats arranged in semicircular arcs from left to right
- Individual seats rendered as dots or small segments
- Legend should display party names with seat counts
- Optional: highlight majority threshold line (e.g., 50%+1 seats)
- Party names are made up and resemble no real party (no ideological family labels such as Green, Labour, Liberal, Conservative, Socialist, Social Democratic, Democratic, Republican, National, People's, or Christian)
- Seat counts are made up, and no real country, parliament, election, or politician is named anywhere in the chart
- Party colors come from the chart palette in its order, never picked to imitate a real party's color, and the blocks follow the data order rather than a left-right political spectrum

## What a good version looks like

- A good version shows: one mark per seat, a dot or a small segment, all of one size, arranged in concentric semicircular arcs that together form a half circle; a seat's position is layout, not data, so there are no axes or grid.
- A good version shows: each party's seats in that party's color and equal in number to its seat count, grouped as one contiguous block, with the blocks following one another from left to right across the arcs.
- A good version shows: a legend that lists the party names with their seat counts, as the Notes ask, with every party's color distinguishable from its neighbors and from the page in both themes.
- A good version shows: the majority threshold line the Notes allow, if drawn, at the seat count it marks and labeled, with its line and label clear of the seat marks.
- A good version shows: the basic variant's single chamber: besides the majority threshold line the Notes allow, no other reference lines, highlighted seats, coalition bands or other highlights, callouts, or second chamber or period for comparison.
- Expected, not a defect: blocks of very different size, including a party with a handful of seats, block boundaries that are stepped rather than straight because the arcs hold different numbers of seats, and small seat marks in a large chamber.
