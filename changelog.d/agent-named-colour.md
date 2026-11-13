### Fixed

- **A colour you name stays your choice.** In the chat of "Use with my
  data", "make the bars orange" came out in the nearest colour of the house
  palette, an ochre, without a word, and there was no way to the orange
  itself. A colour word is still drawn as the palette's nearest colour, but
  the reply now says which one and asks whether that is fine. Say that you
  want the colour itself ("no, a real orange") and the plot draws it, as
  the value the name has in CSS, so the same word gives the same colour in
  every library. A value such as `#FF8800` is drawn exactly as given, with
  no question. (#13084)
- **A plot draws each value as it is.** A plot had shown negative amounts
  as positive bars, and no line said so. The plot rules protected the rows
  and not the values. A bound value is now drawn as it is in the data: no
  absolute value, no flipped sign, no clipped or converted value, unless
  the plot type computes its marks or places them by its own geometry, or
  the user asks for it, and a change the user asks for is named in the
  plot's notes. (#13084)
