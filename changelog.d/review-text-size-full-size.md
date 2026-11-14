### Changed

- **The review judges text size in the full-size render, against the style
  guide's own sizes.** VQ-01 asked for text that stays legible when the image
  is scaled down to about 400 px. The style guide's tick labels (8 pt, about
  44 px of 3200) are about 5 px there, so the two rules contradicted each
  other. The rubric now says where to judge (the full-size render, in both
  themes; a reduced view is never the test) and what is too small: text
  below the size the style guide's "Text Sizes" and the library's prompt give
  it, when it reads small beside the plot's other text or for what it
  carries. Text at or above its reference is never too small. The review
  prompt's example defect lines no longer argue with the thumbnail, and the
  style guide's own test names the full-size render. Its text sizes get a
  heading of their own, with ggplot2, Makie and MUI X, which the table left
  out. Its "Common Mistake" note no longer gives matplotlib `fontsize=10` as
  a size that is too small: that is the table's own axis-title size, and in
  an earlier measurement 27 of 29 VQ-01 lines of the chat's reviewer followed
  the note. In the catalogue 26 of the 536 reviews since
  2026-10-15 lose a point on VQ-01; 23 of them cite the thumbnail, about 16
  for text below its reference (still a defect) and 5 for text at it.

### Fixed

- **The agent chat's reviewer reads the style guide's text sizes.** A review
  line under VQ-01 sends a plot to a second round at any score, about 45
  seconds. The reviewer read the rubric's 400 px test without the sizes the
  rubric points to, so 8 pt tick labels, the size the catalogue plot already
  had, could count as too small. Of the 46 live plot runs from 2026-11-09 to
  2026-11-13, a visible-defect line forced a second round in 12; VQ-01 was
  among the lines in 9 of them and the only one in 3, and it was still there
  after the repair in 4. The reviewer and the offline scorer now get the
  style guide's "Text Sizes" behind the rubric, cut verbatim like the rubric
  itself, so text at the house size is no defect by what they read. The
  adapter already had the whole style guide.
