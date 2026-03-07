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
