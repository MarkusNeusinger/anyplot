### Fixed

- **A regeneration keeps a square plot on the square canvas.** The generator
  treats an old file's figure size as historical and resets it, and three
  matplotlib regenerations reset a square figure that an old tight crop had
  trimmed to an odd size to the landscape default: a Venn diagram and two
  equal-axes plots shrank to the middle of the canvas, with empty bands at
  both sides, and two of them merged as judged worse. The orientation now
  stays square when the previous render is square or nearly so, or the plot
  keeps a 1:1 aspect; the square list names Venn diagrams, circle packing,
  polar charts and equal-axes plots.
