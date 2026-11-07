### Changed

- **On a phone the plot button stands under the message box.** Below the
  page's phone width (the theme's `sm`, 600 px) the composer row stacks the
  box on a line of its own and the plot button under it at the full width, so
  the box's placeholder reads at 390 px instead of "ask about yo…". From `sm`
  up nothing changes. The order stays box first for the eye, the DOM and Tab;
  the plot button keeps one text size at every width, and the assistant's
  instructions say "the plot button by the message box", true at both widths.
  (#12603)
