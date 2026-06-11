# curve-power-duration: Mean-Maximal Power Duration Curve

## Description

A power duration curve plots an athlete's best mean-maximal power output (watts) against effort duration on a logarithmic time axis spanning roughly 1 second to several hours. Each point answers "what is the highest average power this rider could sustain for exactly this long?", producing a characteristic monotonically decreasing decay curve. A critical power (CP) model is fitted and overlaid, decomposing performance into an aerobic asymptote (CP) and a finite anaerobic work capacity (W′). The chart is a cornerstone of cycling and endurance sports analytics for profiling rider strengths, tracking fitness, and setting training zones.

## Applications

- Cycling performance analysis: profiling a rider as a sprinter, puncheur, or time-trialist by the shape of their power-duration curve and the height of its short- vs long-duration regions
- Critical power testing: fitting the CP/W′ model to a handful of maximal efforts to estimate sustainable aerobic power and anaerobic reserve
- Training prescription: deriving Functional Threshold Power (FTP) and training zones from the 20-minute and 60-minute power points
- Longitudinal fitness tracking: overlaying curves from different training blocks or seasons to visualize gains across the durational spectrum

## Data

- `duration_s` (float) - Effort duration in seconds, log-spaced from ~1 s to ~18,000 s (5 hours)
- `power_w` (float) - Best mean-maximal power output in watts sustained for that duration (monotonically non-increasing as duration grows)
- `model_power_w` (float) - Critical power model prediction in watts for each duration, e.g. P(t) = CP + W′/t
- Size: 30-60 points for the empirical curve (log-spaced durations), plus the fitted model line
- Example: Synthetic well-trained cyclist with CP ≈ 280 W and W′ ≈ 20,000 J, peaking near 1,100 W for a 1 s sprint and decaying toward ~280 W over multi-hour efforts

## Notes

- X-axis MUST be logarithmic in time (seconds), with human-readable tick labels (e.g. 1s, 5s, 30s, 1min, 5min, 20min, 1h)
- Plot the empirical mean-maximal curve as the primary series and overlay the fitted critical power model as a distinct (e.g. dashed) line
- Annotate reference durations with vertical markers and labels: 5 s sprint, 1 min, 5 min, and 20 min (FTP proxy); optionally annotate the corresponding power values
- Optionally draw a horizontal asymptote line at the critical power (CP) value with a label
- The empirical curve is monotonically non-increasing; the model fit smoothly approaches the CP asymptote at long durations
- Use a clean sports-science / analytics style; ensure the log-x decay shape and the model fit are both clearly legible
- Distinct from `line-load-duration` (electrical grid load duration curve) — this is the cycling/endurance power-vs-duration curve
