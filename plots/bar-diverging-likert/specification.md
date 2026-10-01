# bar-diverging-likert: Likert Scale Diverging Bar Chart

## Description

A diverging stacked bar chart designed for Likert scale survey responses (e.g., Strongly Disagree to Strongly Agree). Bars diverge from a central neutral point, with negative responses (Disagree, Strongly Disagree) extending left and positive responses (Agree, Strongly Agree) extending right. This layout makes it easy to compare overall agreement levels across multiple survey questions at a glance.

## Applications

- Visualizing survey results in social science research with multi-point agreement scales
- Displaying employee satisfaction and engagement survey outcomes across departments or questions
- Analyzing customer feedback and Net Promoter Score distributions
- Comparing course evaluation responses across educational assessment items

## Data

- `question` (categorical) - Survey question or item label
- `strongly_disagree` (numeric) - Percentage of responses in the "Strongly Disagree" category
- `disagree` (numeric) - Percentage of responses in the "Disagree" category
- `neutral` (numeric) - Percentage of responses in the "Neutral" category
- `agree` (numeric) - Percentage of responses in the "Agree" category
- `strongly_agree` (numeric) - Percentage of responses in the "Strongly Agree" category
- Size: 5-20 questions
- Example: Employee engagement survey with 10 questions rated on a 5-point Likert scale

## Notes

- Center the chart on the neutral response category, splitting it evenly across the midpoint
- Use a diverging color scheme (e.g., red-to-blue or orange-to-teal) with a muted tone for neutral
- Sort questions by net agreement (agree + strongly agree minus disagree + strongly disagree) for easy comparison
- Show percentage labels inside bar segments where space permits
- Use horizontal orientation so question text is readable

## What a good version looks like

- A good version shows: one horizontal bar per question, as the Notes ask, its segments in scale order from strongly disagree at the left end to strongly agree at the right end, each segment's length equal to its percentage.
- A good version shows: every bar centered on its neutral segment, split evenly across one shared midpoint as the Notes ask, so disagreement extends left of that line and agreement extends right of it in every row.
- A good version shows: a diverging color scheme, as the Notes ask: one hue for the disagree side and a contrasting one for the agree side, stronger for the two strong responses, and a muted tone for neutral, the same in every bar and named in a legend.
- A good version shows: the questions sorted by net agreement, as the Notes ask, so the rows run from the most agreed to the least agreed or the reverse.
- A good version shows: percentage labels inside the segments that have room for them, as the Notes ask, readable against their own fill in both themes.
- Expected, not a defect: bars whose left and right ends are ragged because they share a midpoint rather than an edge, most bars leaning to one side, and narrow segments that are left unlabeled.
