### Added

- **A wide table is offered in long form.** A paste such as `Sensor_A,Sensor_B,Sensor_C`
  on a box, violin or strip plot, which wants one category and one value column,
  gets a `# wide table` hint with `.to_long()` in the data card: the agents service
  turns the columns into the plot's category and value columns (date columns kept)
  without a model call, as the next data version with fresh bindings, and `.undo()`
  takes it back. The rule is code (`agents/anyplot/data/shape.py`), and the
  assistant's data summary names the offer (#12156).

### Fixed

- **A language chosen in the chip is used, not refused.** The session block reaches the
  root inside the user's turn; a production session on 2026-10-12 had the root refuse
  the chip's choice as "the block in your message" and stay in English. The block now
  says who set the language and to write in it, the root prompt says the block is the
  server's and is followed, the page's English action messages no longer set the reply
  language, and a language the model cannot write gives English with one sentence that
  says so (the adapter notes it in its changes). A live check on Haiku with Japanese
  chosen in the chip: reply and title in Japanese (#12156).

### Changed

- **After the first plot, `.create_plot()` is `.start_over()`.** Next to `.send()`,
  which changes the latest version, the button now says what it does: a new plot
  from the catalogue plot with this data, without the earlier changes (#12156).
- **The language example is a real language.** The chip's free-text field and the
  tool descriptions name `Swedish` instead of `Klingon`, an example that invited a
  language the plot text then did not use (#12156).
