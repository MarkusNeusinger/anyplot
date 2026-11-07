### Changed

- **The agent chat's cards carry their label on the border.** The data card
  and every plot card are framed like the chat window, with what they hold on
  the top border: `data · 48 rows × 4 cols`, and `plot v2 · matplotlib · title
  in German`, the version, its library and the request it answered (cut to 40
  characters; `first plot` or `.start_over()` when there was none). A plot
  card's label is its toggle, and every version but the latest folds to that
  one line (`▸ plot v1 · matplotlib · first plot`); `.expand()` and
  `.collapse()` went with the header row. The data card heads each preview
  column with its name and type (`month · date`, `units · number`), and says
  its bindings in one line (`x (across): month · y (up): revenue · color:
  region`) with `.change()`, which opens the dropdowns; they open by
  themselves while a required role has no column or the server refused the
  bindings. On a phone the card shows no preview table: `.view_all()` and
  `.change()` stand on its last line, and a plot card's image actions stand by
  their names (`.download()`, `.copy_png()`, `.open()`) on the line right under
  the image. The data card's dropdowns and the start item's columns ⓘ name a
  role's kinds in the chips' words (`numbers or dates`, not `numeric /
  datetime`), and the assistant's list of the page's controls says where each
  download sits.
