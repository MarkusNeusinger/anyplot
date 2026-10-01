# spirometry-flow-volume: Spirometry Flow-Volume Loop

## Description

A pulmonary function test visualization that plots airflow rate (L/s) against lung volume (L) during forced expiration and inspiration, forming a characteristic loop shape. The expiratory limb rises sharply to Peak Expiratory Flow (PEF) then declines, while the inspiratory limb forms a more symmetric curve below the x-axis. This plot is essential for diagnosing obstructive and restrictive lung diseases by comparing measured loops against predicted normal values.

## Applications

- Pulmonology clinics diagnosing obstructive (e.g., asthma, COPD) vs restrictive (e.g., pulmonary fibrosis) lung disease by analyzing loop shape distortions
- Respiratory therapy departments monitoring treatment effectiveness by overlaying pre- and post-bronchodilator flow-volume loops
- Occupational health screening programs assessing lung function in workers exposed to respiratory hazards
- Medical education teaching respiratory physiology and spirometry interpretation to students

## Data

- `volume` (float) - Lung volume in liters (L), x-axis, representing cumulative exhaled/inhaled volume
- `flow_expiratory` (float) - Expiratory airflow rate in liters per second (L/s), positive values forming the upper limb
- `flow_inspiratory` (float) - Inspiratory airflow rate in liters per second (L/s), negative values forming the lower limb
- `volume_predicted` (float) - Predicted normal volume values for overlay reference loop
- `flow_predicted_expiratory` (float) - Predicted normal expiratory flow values
- `flow_predicted_inspiratory` (float) - Predicted normal inspiratory flow values
- Size: ~100-200 points per limb for smooth curves
- Example: Spirometry test data with measured and predicted normal flow-volume curves

## Notes

- The expiratory limb (upper portion) should show a sharp rise to PEF followed by a roughly linear decline
- The inspiratory limb (lower portion) should appear as a more symmetric, U-shaped curve below the zero flow line
- Mark Peak Expiratory Flow (PEF) with a labeled point or annotation
- Annotate key clinical values: FEV1, FVC, and PEF with their numeric values (use a text box or legend)
- Include a dashed predicted normal loop overlay for comparison
- X-axis label: "Volume (L)", Y-axis label: "Flow (L/s)"
- The flow-volume loop should form a closed shape connecting expiratory and inspiratory limbs
- Use distinct styling (e.g., solid line for measured, dashed for predicted) to differentiate curves

## What a good version looks like

- A good version shows: flow in L/s against volume in L, with the expiratory limb above the zero flow line and the inspiratory limb below it, the two joined into one closed loop, as the Notes ask.
- A good version shows: an expiratory limb that rises sharply to PEF and then declines roughly linearly, and an inspiratory limb that is a more symmetric, U-shaped curve, as the Notes ask, both drawn through their data values.
- A good version shows: Peak Expiratory Flow marked with a labeled point or annotation, as the Notes ask, sitting on the highest point of the measured expiratory limb.
- A good version shows: FEV1, FVC and PEF with their numeric values in a text box or legend, as the Notes ask, placed clear of the loop and agreeing with it where the loop shows them (PEF with the peak, FVC with the loop's width).
- A good version shows: the predicted normal loop as a dashed overlay, as the Notes ask, styled so that the measured and the predicted loop are told apart at once and the measured one stays the more prominent.
- Expected, not a defect: a lopsided loop with a tall early expiratory peak over a shallower rounded inspiratory limb, empty corners of the plot area, a measured loop that lies inside or departs from the predicted one, and FEV1 given only as a number, since the loop has no time axis.
