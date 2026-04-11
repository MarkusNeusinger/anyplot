# area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics

## Description

A cumulative flow diagram (CFD) displays the cumulative count of items in each workflow stage as stacked areas over time. Each band represents a stage (e.g., Backlog, In Progress, Done), and the vertical distance between two adjacent band boundaries shows the number of items currently in that stage (work-in-progress). This is a key visualization in Lean and Agile project management for identifying bottlenecks, monitoring throughput, and assessing flow efficiency across a delivery pipeline.

## Applications

- Monitoring Kanban board throughput and cycle time to assess team delivery performance
- Identifying bottlenecks in software development pipelines by spotting widening or narrowing bands
- Tracking manufacturing workflow stages over time to optimize production flow
- Visualizing support ticket lifecycle stages to measure resolution efficiency

## Data

- `date` (date) - time axis representing the reporting period
- `stage` (categorical, ordered) - workflow stage name in process order (e.g., Backlog, Analysis, Development, Testing, Done)
- `count` (int) - cumulative number of items that have entered or passed through that stage by the given date
- Size: 30-365 days, 4-8 stages
- Example: daily cumulative item counts across a Kanban board with stages Backlog, In Progress, Review, Done over 90 days

## Notes

- Stages must be stacked in workflow order: earliest stage (e.g., Backlog) on top, latest stage (e.g., Done) on bottom
- The vertical distance between two adjacent band boundaries represents the number of items currently in that stage (WIP)
- Cumulative counts are monotonically non-decreasing; each stage's count should always be greater than or equal to the count of the next stage in the workflow
- Widening bands indicate growing WIP or bottlenecks; narrowing bands indicate stages draining faster than they fill
- Use a sequential or distinct color palette where earlier stages are visually distinguishable from later stages
- Include a legend identifying each workflow stage
- X-axis should display date labels at reasonable intervals
