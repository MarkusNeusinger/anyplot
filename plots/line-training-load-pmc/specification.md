# line-training-load-pmc: Training Load Performance Management Chart

## Description

A Performance Management Chart (PMC), popularized by TrainingPeaks, summarizes an endurance athlete's training history on a single shared time axis. Two exponentially-smoothed lines track Chronic Training Load (CTL, "fitness", ~42-day time constant) and Acute Training Load (ATL, "fatigue", ~7-day time constant), while a filled area or band shows Training Stress Balance (TSB, "form" = CTL − ATL) above and below a zero baseline. Daily Training Stress Score (TSS) values appear as points or thin vertical bars, giving the raw workout intensity behind the smoothed trends. The chart reveals whether an athlete is building fitness, accumulating fatigue, or freshening up (positive form) for a target event.

## Applications

- Coaches periodizing an athlete's season to peak fitness while managing fatigue before a key race
- Cyclists and runners deciding rest vs. overload by reading current form (TSB) against rising fitness (CTL)
- Sports scientists studying training monotony, ramp rate, and injury/overtraining risk from acute:chronic load
- Self-coached endurance athletes tracking long-term progression and taper timing across a training block

## Data

- `date` (datetime) - Calendar day across the training period, one row per day
- `tss` (numeric) - Daily Training Stress Score, the raw load for that day (0 on rest days)
- `ctl` (numeric) - Chronic Training Load / fitness, ~42-day exponentially weighted average of TSS
- `atl` (numeric) - Acute Training Load / fatigue, ~7-day exponentially weighted average of TSS
- `tsb` (numeric) - Training Stress Balance / form, computed as previous-day CTL minus previous-day ATL
- Size: 90-365 daily points (a typical training block or full season)
- Example: One athlete's daily TSS over a 6-12 month build, with CTL/ATL/TSB derived via standard EWMA formulas

## Notes

- Plot CTL and ATL as smooth lines on the primary axis (e.g. blue for fitness, purple/magenta for fatigue); CTL should look smoother and lag ATL
- Render TSB as a filled area or band relative to a zero baseline, ideally two-toned (positive form = fresh/blue, negative = fatigued/red); it may sit on a secondary axis since it oscillates around zero
- Draw daily TSS as light points or thin bars near the bottom so they read as the raw input without dominating the smoothed lines
- Keep a single shared time (date) x-axis; use a clear legend distinguishing Fitness (CTL), Fatigue (ATL), Form (TSB), and daily TSS
- A horizontal reference line at TSB = 0 helps separate "fresh/positive form" from "fatigued/negative form"
- If the library supports it, a secondary y-axis for TSB keeps it readable against the larger CTL/ATL magnitudes; otherwise scale all series onto one axis
