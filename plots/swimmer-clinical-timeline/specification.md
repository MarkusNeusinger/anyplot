# swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines

## Description

A swimmer plot displays individual patient timelines as horizontal bars, commonly used in clinical oncology to visualize treatment duration, response events, and disease progression across a study cohort. Each bar represents one patient, typically sorted by treatment duration, with symbols or color changes marking key clinical events such as partial response, complete response, or progressive disease. This plot is standard in clinical trial publications and regulatory submissions for conveying patient-level longitudinal outcomes at a glance.

## Applications

- Visualizing treatment response timelines for patients in an oncology drug trial, showing when each patient achieved response or experienced progression
- Comparing duration of therapy across patients in a Phase II clinical study, highlighting differences between treatment arms
- Presenting patient-level safety and efficacy data in regulatory submission documents and medical conference posters

## Data

- `patient_id` (string) - Unique identifier for each patient (e.g., "PT-001")
- `duration` (numeric) - Total time on study or treatment in weeks/months
- `events` (list of objects) - Clinical events with `time` (numeric), `event_type` (categorical: "partial_response", "complete_response", "progressive_disease", "adverse_event", "ongoing"), and optional `label` (string)
- `group` (categorical, optional) - Treatment arm or patient subgroup for color coding
- Size: 15-60 patients (typical clinical study cohort)
- Example: Simulated Phase II oncology trial with 25 patients across two treatment arms, including response and progression events

## Notes

- Bars should be horizontal and sorted by duration (longest at top or bottom, consistently)
- Use distinct markers/symbols for different event types (e.g., triangle for partial response, star for complete response, diamond for progression)
- Ongoing patients (still on treatment at data cutoff) should be visually distinguished with an arrow or open-ended bar
- Include a clear legend explaining all event symbols and color coding
- X-axis should show time units (weeks or months) with a descriptive axis label
- Patient IDs should appear on the y-axis
- Color-code bars by treatment arm or response status if group data is provided
