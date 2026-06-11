# bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart

## Description

A vertical bar chart showing the time spent in each heart rate training zone (Z1–Z5) during a workout or training period. Each bar uses the conventional zone color semantics (grey for Z1 recovery, blue for Z2 endurance, green for Z3 aerobic, orange for Z4 threshold, red for Z5 maximum) and is annotated with its duration, making the distribution of training intensity immediately readable. This is the standard summary chart found in fitness platforms such as Garmin, Strava, and Polar, and it reveals at a glance whether a session was easy, balanced, or high-intensity.

## Applications

- Endurance training: reviewing a single run or ride to confirm time was spent in the intended intensity zone (e.g. mostly Z2 for a base session)
- Coaching and training-load analysis: summarizing a week or training block to balance easy vs. hard time and avoid overtraining
- Fitness app workout summaries: presenting per-zone duration in the familiar Garmin/Strava/Polar style after an activity
- Polarized-training assessment: checking the 80/20 split between low- and high-intensity zones

## Data

- `zone` (str) - Heart rate zone label, ordered Z1 to Z5 (e.g. "Z1", "Z2", ... or "Recovery", "Endurance", "Aerobic", "Threshold", "Maximum")
- `minutes` (float) - Time spent in the zone, in minutes (may also be seconds; one duration value per zone)
- `hr_low` (int, optional) - Lower heart rate boundary of the zone in bpm or % of max HR (for zone boundary annotations)
- `hr_high` (int, optional) - Upper heart rate boundary of the zone in bpm or % of max HR
- Size: exactly 5 zones (Z1–Z5); optionally fewer if the workout did not reach higher zones
- Example: a 60-minute tempo run with durations like Z1: 8 min, Z2: 22 min, Z3: 15 min, Z4: 12 min, Z5: 3 min

## Notes

- Use the conventional per-zone colors in order: Z1 grey, Z2 blue, Z3 green, Z4 orange, Z5 red
- Keep zones in fixed Z1→Z5 order on the x-axis (do not sort by duration)
- Label each bar with its duration (e.g. formatted as "MM:SS" or "X min")
- Optionally annotate each bar or axis tick with the zone's HR boundary range (bpm or % of max HR)
- Y-axis represents time (minutes or seconds); a horizontal layout is an acceptable alternative
- Fully static-renderable; a clear legend or zone-name labels help readers unfamiliar with Z1–Z5 shorthand
