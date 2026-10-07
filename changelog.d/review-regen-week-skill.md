### Added

- **Weekly regen review skill.** The `review-regen-week` project skill turns a week of `daily-regen`
  regenerations into a dated report: a bundled `collect_week.py` gathers every regen PR's gate record,
  parsed review, write-back and pair artifact into JSON, flags what needs a look (merges without a
  carrier, silent deductions, stranded write-backs, big re-score drops, identical review vectors), and
  picks a render sample. The skill sets targets for each metric, classifies findings by where the fix
  belongs (spec, rubric, generator, gate, workflow, one-off regen), and ships a lessons file that
  distills the scoring and gate work so a reviewer can tell expected behavior from real problems.
