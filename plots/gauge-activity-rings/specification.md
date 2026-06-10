# gauge-activity-rings: Activity Rings Progress Chart

## Description

An activity rings chart displays goal completion for several metrics at once using concentric radial progress arcs, in the style popularized by fitness trackers. Each ring is a partial arc with rounded end caps that starts at the top (12 o'clock) and sweeps clockwise in proportion to how close the metric is to its goal, with a distinct color per metric and a faint background track showing the full circle. It is instantly recognizable and ideal for at-a-glance comparison of progress across a small set of related goals, filling the general radial-progress gap that needle gauges (`gauge-basic`) and polar bars (`polar-bar`) do not cover.

## Applications

- Daily fitness summary showing move, exercise, and stand goal completion on a wearable or health dashboard
- Personal productivity tracker comparing progress toward calories, active minutes, and step targets
- Project or fundraising dashboard showing percent-to-goal for several parallel campaigns
- Onboarding or gamification widgets indicating completion of multiple task categories

## Data

- `metric` (categorical) - Name of each goal/metric, one per ring (e.g., Move, Exercise, Stand)
- `value` (numeric) - Current accumulated value for the metric
- `goal` (numeric) - Target value defining 100% completion for the metric
- `color` (categorical, optional) - Distinct color per ring; falls back to a qualitative palette
- Size: 2-5 rings (3 is the canonical/iconic count)
- Example: Move 420/600 kcal, Exercise 25/30 min, Stand 9/12 hr

## Notes

- Draw each ring as a thick partial arc starting at 90° (top) and progressing clockwise; use rounded line caps for the iconic look
- Behind each colored arc, render a faint full-circle track (typically the ring color at low opacity) so remaining progress is visible
- Fraction = value / goal; clamp the visible sweep to 360° but allow values that exceed the goal to be indicated (e.g., full ring plus a label) where the library permits
- Order rings from outer (first/primary metric) to inner with consistent gap/thickness; keep stroke widths equal
- Optional center label area can show a headline summary (e.g., percent complete or the primary metric); per-ring labels or a legend map colors to metric names
- Keep the aspect ratio square so rings remain circular; equal axis scaling is required
