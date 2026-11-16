### Fixed

- **A title you replace no longer comes back.** In the chat of "Use with my
  data", the plot memory kept a remembered title after you set a new one
  that the plot drew, and the card still listed the old title as kept. A
  later change could draw the old title again. Now, when a plot draws a
  title or axis label you wrote as that part's whole text and no longer
  draws the remembered text whole anywhere, the new text replaces the
  remembered entry, also when it only lengthens the remembered one. A
  subtitle is replaced only in libraries whose text check reports a
  subtitle, which matplotlib and seaborn don't. In plotnine, whose text
  check reports none of these parts, nothing is replaced. Under a figure
  title above an axes title, or on a figure of several panels, only a
  figure title you wrote replaces the title. An x or y axis label is never
  replaced where the plot draws several different labels for that axis, as
  on panels with labels of their own or with a second y axis. This never
  adds an entry to an empty memory. A title filed with the target `plot`
  and one filed without are now one title. (#13143)
- **The plot card says which remembered decisions the plot did not use.**
  A remembered decision whose text the plot does not draw now ends the
  card's decisions line as `not used: …` instead of standing under
  `kept:`. It stays in the memory, since only you remove a decision. A
  decision without a text, one written before the plot language changed,
  and every decision in a library whose reviewer checks the texts in the
  image still count as kept, so `not used:` appears on matplotlib, seaborn
  and plotnine plots only. (#13143)
