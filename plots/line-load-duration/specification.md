# line-load-duration: Load Duration Curve for Energy Systems

## Description

A load duration curve displays electrical power demand (MW) sorted from highest to lowest across all hours of a year (8,760 hours), forming a monotonically decreasing curve. It is a fundamental tool in power system planning, revealing the proportion of time that load exceeds a given level. The curve naturally segments into peak, intermediate, and base load regions, helping utilities determine the optimal generation capacity mix. The area under the curve represents total annual energy consumption.

## Applications

- Power system planning: determining the optimal mix of base load, intermediate, and peaking generation capacity based on load profile shape
- Utility rate design: calculating load factors and capacity utilization to inform pricing structures
- Renewable energy assessment: evaluating capacity credit and understanding how variable generation sources align with demand patterns
- Energy policy analysis: comparing load duration curves before and after demand-side management programs to quantify their impact

## Data

- `hour` (integer) - Rank-ordered hour index from 0 to 8759, representing position along the sorted duration axis
- `load_mw` (float) - Electrical power demand in megawatts for each hour, sorted in descending order
- Size: 8,760 data points (one per hour of a standard year)
- Example: Synthetic annual hourly load profile for a mid-sized utility, with peak demand around 1,200 MW and base load around 400 MW

## Notes

- The curve must be monotonically decreasing (load values sorted from highest to lowest)
- Shade or fill distinct regions under the curve to distinguish base load (rightmost, always-on), intermediate load (middle), and peak load (leftmost, brief spikes)
- Add horizontal dashed lines with labels indicating generation capacity tiers (e.g., base load capacity, intermediate capacity, peak capacity)
- Annotate or label the three load regions directly on the plot
- Include the total energy consumption value (area under curve) as a text annotation
- Use a clean, professional style appropriate for engineering reports

## What a good version looks like

- A good version shows: load plotted against duration, the hours of the year ranked from the highest load to the lowest rather than in calendar order, as one curve that never rises from left to right, as the Notes require.
- A good version shows: a load axis that starts at zero and a duration axis spanning the whole year, so the area under the curve reads as the year's energy.
- A good version shows: the area under the curve filled as three distinct regions, as the Notes ask: peak load where the curve spikes at the left, base load along the always-on level at the right, and intermediate load between them, each labeled directly on the plot and distinguishable in both themes.
- A good version shows: horizontal dashed lines marking the generation capacity tiers, each with its own label, as the Notes ask, the labels clear of the curve and of the region labels.
- A good version shows: the total energy consumption as a text annotation with its unit, as the Notes ask, consistent with the area under the curve.
- Expected, not a defect: a steep, narrow spike at the left, a long gently sloping middle and a drop at the far right, a peak region that is only a sliver, and a curve far smoother than hourly load, because sorting removes the daily and seasonal swings.
