### Fixed

- **A colour you name is the colour you get.** In the chat of "Use with my
  data", "make the bars orange" came out in the nearest colour of the house
  palette, an ochre, while a hex value such as `#FF8800` was taken as given.
  A colour the user names, by a word or by a value, is now drawn as that
  colour: a named one as the value the name has in CSS, so the same word
  gives the same colour in every library. The palette stays the choice for
  every colour the user did not name. (#13084)
- **A plot draws each value as it is.** A plot had shown negative amounts
  as positive bars, and no line said so. The plot rules protected the rows
  and not the values. A bound value is now drawn as it is in the data: no
  absolute value, no flipped sign, no clipped or converted value, unless
  the plot type computes its marks or places them by its own geometry, or
  the user asks for it, and a change the user asks for is named in the
  plot's notes. (#13084)
