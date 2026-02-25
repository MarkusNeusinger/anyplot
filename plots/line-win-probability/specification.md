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
