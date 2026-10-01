# line-win-probability: Win Probability Chart

## Description

A win probability chart shows how each team's likelihood of winning evolves over the course of a game. The line starts near 50% and fluctuates based on scoring events, ultimately reaching 100% or 0% at game end. The area above and below the 50% baseline is filled with team colors to convey momentum at a glance. This visualization is widely used across major sports for post-game analysis and live broadcasting.

## Applications

- Visualizing game momentum shifts and identifying critical turning points in close contests
- Sports broadcasting overlays showing real-time win probability during live games
- Post-game journalism and analysis highlighting the most impactful plays
- Evaluating team resilience and performance under pressure across a season

## Data

- `game_time` (numeric) - Elapsed time in minutes or play/event number from start to end of game
- `win_probability` (numeric) - Probability of the home team winning, ranging from 0 to 1
- `event` (categorical, optional) - Labels for key scoring events or plays to annotate on the chart
- Size: 50-300 data points per game
- Example: An NFL game with play-by-play win probability from a model, annotated with touchdowns and field goals

## Notes

- Y-axis should range from 0% to 100% with a prominent horizontal reference line at 50%
- Fill the area above 50% with the home team color and below 50% with the away team color
- Annotate key scoring events (touchdowns, goals, runs) that caused significant probability swings
- Display the final score in a corner annotation or subtitle
- X-axis represents game progression (time or play number) with appropriate period/quarter markers

## What a good version looks like

- A good version shows: one win probability line joining the values in game order, on a y axis fixed to the full range from 0 to 100 percent, as the Notes ask, never cropped to the range the line happens to cover.
- A good version shows: a prominent horizontal reference line at 50 percent, with the area between it and the line filled in the home team color where the line is above it and the away team color where it is below, the fill changing exactly where the line crosses.
- A good version shows: the key scoring events annotated at their position on the line, as the Notes ask, each label tied to the swing it caused and readable in both themes.
- A good version shows: an x axis of game progression with period or quarter markers, as the Notes ask, so each swing can be placed in the game.
- A good version shows: the final score in a corner annotation or subtitle, as the Notes ask, kept clear of the line and the fills.
- Expected, not a defect: abrupt jumps at scoring events, long flat stretches, a line that crosses the 50 percent line many times or not at all, unequal fill areas for the two teams, a start near but not exactly at 50 percent, and a line that ends pinned at the top or bottom of the axis.
