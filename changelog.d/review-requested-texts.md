### Fixed

- **A ggplot2 plot that showed the requested text still needed attention.**
  R writes no probe, so the agent chat could not check a text the user asked
  for, such as a title or an axis label, and every such request shipped as
  `needs attention` with "the requested texts could not be checked", although
  the image showed the text (live test of 2026-10-29). The reviewer now
  checks these texts in the image, in the review call it already makes
  (owner decision of 2026-10-29). Only a render without drawn texts on a
  runtime that opts in (`RuntimeAdapter.review_texts`, R today) sends the texts
  to the reviewer, so the reviewer prompt and every review request of a render
  with the probe stay unchanged. The reviewer reports a text it cannot find as
  an `SC-04` line that quotes it (`SC-02` for a number format), and the
  pipeline handles that line like the probe's miss: under
  `AGENT_EXPECT_CHECK=repair` it sends the round to the repair whatever the
  points, and if no round fixes it, the plot ships with the line and the text
  in `requested_not_found`. The "could not be checked" note now appears only
  when no readable review answered for the texts.
