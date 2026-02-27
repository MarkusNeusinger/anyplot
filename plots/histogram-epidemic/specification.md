# histogram-epidemic: Epidemic Curve (Epi Curve)

## Description

An epidemic curve (epi curve) is a histogram showing the number of new disease cases over time, plotted by date of symptom onset. The shape of the curve reveals the outbreak pattern: a sharp peak indicates a point source, successive waves suggest propagated transmission, and a plateau indicates continuous exposure. It is fundamental to epidemiological investigation and public health surveillance.

## Applications

- Tracking disease outbreaks and identifying transmission patterns (e.g., foodborne illness traced to a single event)
- Monitoring pandemic progression such as COVID-19 or influenza waves across regions
- Determining outbreak source type and estimating incubation periods from curve shape
- Public health reporting and real-time surveillance dashboards

## Data

- `onset_date` (date) - Date of symptom onset for each case or aggregated group
- `case_count` (integer) - Number of new cases reported on that date
- `case_type` (categorical, optional) - Classification of cases: confirmed, probable, or suspect
- Size: 30-365 days of daily observations
- Example: Daily COVID-19 case counts by symptom onset date with confirmed/probable classification

## Notes

- Use daily bins for short outbreaks (< 3 months) and weekly bins for longer epidemics
- Stack bars by case classification (confirmed, probable, suspect) using distinct colors
- Mark key intervention events (e.g., lockdown start, vaccination campaign) with annotated vertical lines
- X-axis should show dates with appropriate tick intervals; y-axis shows case counts
- Consider a secondary y-axis with a cumulative case count line overlay for total burden context
